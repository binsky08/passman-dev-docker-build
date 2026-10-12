#!/usr/bin/env python3
"""
Print Hub retags that keep the previous Passman release reachable.

Before CI moves a rolling tag (nc35_php8.5, …), copy that existing manifest to
<context>-passman-<previous version>. The next merge step then points the
rolling tag at the new build.

Stdout is TSV: source<TAB>destination. Missing destination tags are created by
the workflow; this script does not talk to the registry.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from generate_matrix import (
    has_demo_stage,
    image_name,
    load_registry,
    normalize_release,
    passman_release,
    passman_release_from_text,
    passman_tag,
)


def contexts_from_matrix(payload: dict) -> list[str]:
    seen: list[str] = []
    for row in payload.get("include") or []:
        context = row.get("context")
        if context and context not in seen:
            seen.append(context)
    return seen


def git_file(repo_root: Path, rev: str, path: str) -> str | None:
    if not rev or set(rev) <= {"0"}:
        return None
    proc = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def releases_to_preserve(
    registry: dict,
    context: str,
    previous_text: str | None,
    current_release: str | None,
) -> list[str]:
    """Passman versions whose rolling tag must be copied before it moves."""
    if not current_release:
        return []
    if previous_text is not None:
        previous_release = passman_release_from_text(previous_text)
        if previous_release and previous_release != current_release:
            return [previous_release]
        if previous_release:
            return []
    mapped = normalize_release((registry.get("preserve_rolling_as") or {}).get(context))
    if mapped and mapped != current_release:
        return [mapped]
    return []


def plan_preserves(
    repo_root: Path,
    registry: dict,
    contexts: list[str],
    previous_texts: dict[str, str | None],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    dev_image = image_name(registry, registry["dev_repository"])
    demo_image = image_name(registry, registry["demo_repository"])
    for context in contexts:
        current_release = passman_release(repo_root, context)
        versions = releases_to_preserve(
            registry,
            context,
            previous_texts.get(context),
            current_release,
        )
        images = [dev_image]
        if has_demo_stage(repo_root, context):
            images.append(demo_image)
        for version in versions:
            dest_tag = passman_tag(context, version)
            for image in images:
                pairs.append((f"{image}:{context}", f"{image}:{dest_tag}"))
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--before",
        default="",
        help="Git revision of the previously published Dockerfiles (push: github.event.before)",
    )
    parser.add_argument(
        "--matrix-json",
        default=os.environ.get("MATRIX_JSON", ""),
        help="GitHub Actions matrix JSON (default: MATRIX_JSON env)",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    if not args.matrix_json.strip():
        return 0

    payload = json.loads(args.matrix_json)
    contexts = contexts_from_matrix(payload)
    registry = load_registry(repo_root)
    previous: dict[str, str | None] = {}
    before = args.before
    if not before or set(before) <= {"0"}:
        before = "HEAD~1"
    for context in contexts:
        previous[context] = git_file(repo_root, before, f"{context}/Dockerfile")

    for source, dest in plan_preserves(repo_root, registry, contexts, previous):
        print(f"{source}\t{dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
