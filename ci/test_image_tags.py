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
    def tags_for(self, context: str, target: str) -> list[str]:
        registry = gm.load_registry(ROOT)
        rows = gm.build_rows_for_context(ROOT, registry, context)
        match = next(row for row in rows if row["target"] == target)
        return match["tags"].split(",")

    def test_latest_stack_keeps_rolling_tags_and_adds_passman_suffix(self) -> None:
        dev = self.tags_for("nc35_php8.5", "dev")
        demo = self.tags_for("nc35_php8.5", "demo")
        self.assertEqual(
            dev,
            [
                "binsky/passman-dev:nc35_php8.5",
                "binsky/passman-dev:nc35_php8.5-passman-2.6.4",
                "binsky/passman-dev:latest",
            ],
        )
        self.assertEqual(
            demo,
            [
                "binsky/passman-demo:nc35_php8.5",
                "binsky/passman-demo:nc35_php8.5-passman-2.6.4",
            ],
        )

    def test_master_stack_has_no_passman_suffix(self) -> None:
        dev = self.tags_for("nc34_php8.5", "dev")
        self.assertEqual(dev, ["binsky/passman-dev:nc34_php8.5"])

    def test_older_pin_gets_its_own_suffix(self) -> None:
        dev = self.tags_for("nc33_php8.4", "dev")
        self.assertIn("binsky/passman-dev:nc33_php8.4-passman-2.5.1", dev)
        self.assertNotIn("binsky/passman-dev:latest", dev)


class PreservePlanTests(unittest.TestCase):
    def test_master_to_release_snapshots_mapped_version(self) -> None:
        registry = gm.load_registry(ROOT)
        plan = preserve.plan_preserves(
            ROOT,
            registry,
            ["nc35_php8.5"],
            {"nc35_php8.5": "ENV SETUP_PASSMAN_BRANCH=master\n"},
        )
        self.assertEqual(
            plan,
            [
                (
                    "binsky/passman-dev:nc35_php8.5",
                    "binsky/passman-dev:nc35_php8.5-passman-2.6.3",
                ),
                (
                    "binsky/passman-demo:nc35_php8.5",
                    "binsky/passman-demo:nc35_php8.5-passman-2.6.3",
                ),
            ],
        )

    def test_same_pin_does_not_snapshot(self) -> None:
        registry = gm.load_registry(ROOT)
        plan = preserve.plan_preserves(
            ROOT,
            registry,
            ["nc35_php8.5"],
            {"nc35_php8.5": "ENV SETUP_PASSMAN_BRANCH=2.6.4\n"},
        )
        self.assertEqual(plan, [])

    def test_release_bump_uses_git_pin_not_the_map(self) -> None:
        registry = gm.load_registry(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = root / "nc35_php8.5"
            ctx.mkdir()
            (ctx / "Dockerfile").write_text(
                "FROM scratch\nENV SETUP_PASSMAN_BRANCH=2.6.5\nFROM scratch AS demo\n",
                encoding="utf-8",
            )
            plan = preserve.plan_preserves(
                root,
                registry,
                ["nc35_php8.5"],
                {"nc35_php8.5": "ENV SETUP_PASSMAN_BRANCH=2.6.4\n"},
            )
        self.assertEqual(
            [dest for _, dest in plan],
            [
                "binsky/passman-dev:nc35_php8.5-passman-2.6.4",
                "binsky/passman-demo:nc35_php8.5-passman-2.6.4",
            ],
        )

    def test_matrix_contexts(self) -> None:
        payload = json.loads(
            '{"include":[{"context":"nc35_php8.5","target":"dev"},'
            '{"context":"nc35_php8.5","target":"demo"},'
            '{"context":"nc34_php8.5","target":"dev"}]}'
        )
        self.assertEqual(
            preserve.contexts_from_matrix(payload),
            ["nc35_php8.5", "nc34_php8.5"],
        )


if __name__ == "__main__":
    unittest.main()
