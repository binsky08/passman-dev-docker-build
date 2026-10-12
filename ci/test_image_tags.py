#!/usr/bin/env python3
"""Tag suffix and rolling-tag snapshot plan. Run: python3 ci/test_image_tags.py"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_matrix as gm
import preserve_rolling_tags as preserve

ROOT = Path(__file__).resolve().parents[1]


def write_context(root: Path, context: str, branch: str, demo: bool) -> None:
    body = f"FROM scratch\nENV SETUP_PASSMAN_BRANCH={branch}\n"
    if demo:
        body += "FROM scratch AS demo\n"
    ctx = root / context
    ctx.mkdir()
    (ctx / "Dockerfile").write_text(body, encoding="utf-8")


class ReleaseParseTests(unittest.TestCase):
    def test_unquoted_release(self) -> None:
        text = "ENV SETUP_PASSMAN_BRANCH=2.6.4\n"
        self.assertEqual(gm.passman_release_from_text(text), "2.6.4")

    def test_quoted_release_and_v_prefix(self) -> None:
        self.assertEqual(
            gm.passman_release_from_text('ENV SETUP_PASSMAN_BRANCH="2.5.1"\n'),
            "2.5.1",
        )
        self.assertEqual(gm.normalize_release("v2.6.4"), "2.6.4")

    def test_moving_branch_is_not_a_release(self) -> None:
        self.assertIsNone(
            gm.passman_release_from_text("ENV SETUP_PASSMAN_BRANCH=master\n")
        )


class MatrixTagTests(unittest.TestCase):
    def test_discovered_contexts_follow_pin_and_latest(self) -> None:
        registry = gm.load_registry(ROOT)
        contexts = gm.discover_contexts(ROOT)
        self.assertTrue(contexts)
        dev_image = gm.image_name(registry, registry["dev_repository"])
        demo_image = gm.image_name(registry, registry["demo_repository"])
        latest = registry.get("dev_latest_context")

        for context in contexts:
            release = gm.passman_release(ROOT, context)
            rows = {
                row["target"]: row["tags"].split(",")
                for row in gm.build_rows_for_context(ROOT, registry, context)
            }
            dev_tags = rows["dev"] if gm.has_demo_stage(ROOT, context) else rows[""]
            self.assertEqual(dev_tags[0], f"{dev_image}:{context}")
            suffixed = f"{dev_image}:{gm.passman_tag(context, release)}" if release else None
            if release:
                self.assertIn(suffixed, dev_tags)
            else:
                self.assertFalse(any(f"-{gm.PASSMAN_TAG_MARKER}-" in tag for tag in dev_tags))
            if context == latest:
                self.assertIn(f"{dev_image}:latest", dev_tags)
            else:
                self.assertNotIn(f"{dev_image}:latest", dev_tags)

            if not gm.has_demo_stage(ROOT, context):
                self.assertNotIn("demo", rows)
                continue
            demo_tags = rows["demo"]
            self.assertEqual(demo_tags[0], f"{demo_image}:{context}")
            self.assertNotIn(f"{demo_image}:latest", demo_tags)
            if release:
                self.assertIn(f"{demo_image}:{gm.passman_tag(context, release)}", demo_tags)
            else:
                self.assertFalse(any(f"-{gm.PASSMAN_TAG_MARKER}-" in tag for tag in demo_tags))

        self.assertIn(latest, contexts)


class PreservePlanTests(unittest.TestCase):
    def registry(self, mapped: dict[str, str] | None = None) -> dict:
        registry = {
            "namespace": "binsky",
            "dev_repository": "passman-dev",
            "demo_repository": "passman-demo",
            "dev_latest_context": "example",
        }
        if mapped is not None:
            registry["preserve_rolling_as"] = mapped
        return registry

    def test_unpinned_previous_snapshots_mapped_version(self) -> None:
        context = "example"
        registry = self.registry({context: "1.2.3"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_context(root, context, "9.9.9", demo=True)
            plan = preserve.plan_preserves(
                root,
                registry,
                [context],
                {context: "ENV SETUP_PASSMAN_BRANCH=master\n"},
            )
        dev = "binsky/passman-dev"
        demo = "binsky/passman-demo"
        kept = gm.passman_tag(context, "1.2.3")
        self.assertEqual(
            plan,
            [
                (f"{dev}:{context}", f"{dev}:{kept}"),
                (f"{demo}:{context}", f"{demo}:{kept}"),
            ],
        )

    def test_same_pin_does_not_snapshot(self) -> None:
        context = "example"
        registry = self.registry({context: "1.2.3"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_context(root, context, "9.9.9", demo=False)
            plan = preserve.plan_preserves(
                root,
                registry,
                [context],
                {context: "ENV SETUP_PASSMAN_BRANCH=9.9.9\n"},
            )
        self.assertEqual(plan, [])

    def test_release_bump_uses_git_pin_not_the_map(self) -> None:
        context = "example"
        registry = self.registry({context: "1.2.3"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_context(root, context, "9.9.9", demo=True)
            plan = preserve.plan_preserves(
                root,
                registry,
                [context],
                {context: "ENV SETUP_PASSMAN_BRANCH=8.8.8\n"},
            )
        self.assertEqual(
            [dest for _, dest in plan],
            [
                f"binsky/passman-dev:{gm.passman_tag(context, '8.8.8')}",
                f"binsky/passman-demo:{gm.passman_tag(context, '8.8.8')}",
            ],
        )

    def test_live_preserve_map_matches_discovered_contexts(self) -> None:
        registry = gm.load_registry(ROOT)
        contexts = set(gm.discover_contexts(ROOT))
        dev_image = gm.image_name(registry, registry["dev_repository"])
        demo_image = gm.image_name(registry, registry["demo_repository"])
        for context, version in (registry.get("preserve_rolling_as") or {}).items():
            self.assertIn(context, contexts)
            release = gm.normalize_release(version)
            self.assertIsNotNone(release)
            assert release is not None
            plan = preserve.plan_preserves(
                ROOT,
                registry,
                [context],
                {context: "ENV SETUP_PASSMAN_BRANCH=master\n"},
            )
            if release == gm.passman_release(ROOT, context):
                self.assertEqual(plan, [])
                continue
            kept = gm.passman_tag(context, release)
            self.assertIn((f"{dev_image}:{context}", f"{dev_image}:{kept}"), plan)
            if gm.has_demo_stage(ROOT, context):
                self.assertIn((f"{demo_image}:{context}", f"{demo_image}:{kept}"), plan)

    def test_matrix_contexts(self) -> None:
        payload = json.loads(
            '{"include":[{"context":"one","target":"dev"},'
            '{"context":"one","target":"demo"},'
            '{"context":"two","target":"dev"}]}'
        )
        self.assertEqual(preserve.contexts_from_matrix(payload), ["one", "two"])


if __name__ == "__main__":
    unittest.main()
