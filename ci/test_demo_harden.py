#!/usr/bin/env python3
"""Demo lockdown is applied only on the demo stage. Run via unittest discover."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_matrix as gm

ROOT = Path(__file__).resolve().parents[1]

# Requested system settings. appstoreenabled stays off on dev, so restore skips it.
REQUIRED_KEYS = (
    "knowledgebaseenabled",
    "updatechecker",
    "integrity.check.scheduled",
    "check_for_working_wellknown_setup",
    "config_is_read_only",
    "appstoreenabled",
    "sharing.enable_share_mail",
    "files_external_allow_create_new_local",
    "upgrade.disable-web",
    "bulkupload.enabled",
)


class DemoHardenTests(unittest.TestCase):
    def test_script_sets_every_requested_key_and_blocks_sharing_and_uploads(self) -> None:
        script = (ROOT / "demo-config.sh").read_text(encoding="utf-8")
        for key in REQUIRED_KEYS:
            self.assertIn(key, script)
        self.assertIn("shareapi_enabled", script)
        self.assertIn("--value=no", script)
        self.assertIn('DEMO_USER_QUOTA="100 MB"', script)
        self.assertIn("if [ \"$key\" = \"appstoreenabled\" ]; then", script)

    def test_each_demo_dockerfile_hardens_then_dev_restores(self) -> None:
        demo_contexts = [
            context
            for context in gm.discover_contexts(ROOT)
            if gm.has_demo_stage(ROOT, context)
        ]
        self.assertTrue(demo_contexts)
        for context in demo_contexts:
            text = (ROOT / context / "Dockerfile").read_text(encoding="utf-8")
            self.assertIn("PASSMAN_IMAGE_FLAVOR=demo", text, context)
            self.assertIn("demo-config.sh harden", text, context)
            self.assertIn("PASSMAN_IMAGE_FLAVOR=dev", text, context)
            self.assertIn("demo-config.sh restore", text, context)
            self.assertLess(text.index("harden"), text.index("restore"), context)

    def test_entrypoint_relocks_demo_after_trusted_domain(self) -> None:
        text = (ROOT / "entrypoint.sh").read_text(encoding="utf-8")
        self.assertIn('PASSMAN_IMAGE_FLAVOR:-}" = "demo"', text)
        self.assertLess(text.index("demo-config.sh unlock"), text.index("DEMO_EXTERNAL_FQDN"))
        self.assertLess(
            text.index("DEMO_EXTERNAL_FQDN"),
            text.index("config_is_read_only --type=boolean --value=true"),
        )

    def test_shared_script_change_rebuilds_every_image(self) -> None:
        registry = gm.load_registry(ROOT)
        contexts = set(gm.discover_contexts(ROOT))
        self.assertIsNone(
            gm.expand_affected(ROOT, registry, contexts, ["demo-config.sh"])
        )


if __name__ == "__main__":
    unittest.main()
