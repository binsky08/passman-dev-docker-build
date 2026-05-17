#!/usr/bin/env python3
"""
Discover image build matrix for GitHub Actions: dev (and demo when present) images per context.

Reads ci/registry.json. Emits JSON with { "include": [...], "should_run": true|false } to stdout.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEMO_STAGE = re.compile(r"(?m)^FROM\s+\S+\s+AS\s+demo\s*$")


def load_registry(repo_root: Path) -> dict:
    path = repo_root / "ci" / "registry.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def discover_contexts(repo_root: Path) -> list[str]:
    skip = {"ci", ".git"}
    out = []
    for p in sorted(repo_root.iterdir()):
        if (
            not p.is_dir()
            or p.name.startswith(".")
            or p.name in skip
            or not (p / "Dockerfile").is_file()
        ):
            continue
        out.append(p.name)
    return out


def has_demo_stage(repo_root: Path, context: str) -> bool:
    dockerfile = repo_root / context / "Dockerfile"
    text = dockerfile.read_text(encoding="utf-8", errors="replace")
    return DEMO_STAGE.search(text) is not None


def image_name(registry: dict, repo_suffix: str) -> str:
    ns = registry["namespace"]
    return f"{ns}/{repo_suffix}"


def build_rows_for_context(
    repo_root: Path,
    registry: dict,
    context: str,
) -> list[dict]:
    rows: list[dict] = []
    dev_repo = registry["dev_repository"]
    demo_repo = registry["demo_repository"]
    latest_ctx = registry.get("dev_latest_context")
    dev_image = image_name(registry, dev_repo)

    multi = has_demo_stage(repo_root, context)

    if multi:
        demo_image = image_name(registry, demo_repo)
        demo_tags = f"{demo_image}:{context}"
        rows.append(
            {
                "context": context,
                "build_mode": "stage",
                "target": "demo",
                "tags": demo_tags,
            }
        )

    dev_targets: list[str] = [f"{dev_image}:{context}"]
    if latest_ctx and context == latest_ctx:
        dev_targets.append(f"{dev_image}:latest")

    rows.append(
        {
            "context": context,
            "build_mode": "stage" if multi else "final",
            "target": "dev" if multi else "",
            "tags": ",".join(dev_targets),
        }
    )
    return rows


def normalize_changed_path(line: str) -> str:
    return line.strip().replace("\\", "/")


def expand_affected(
    contexts: set[str],
    changed_files: list[str],
) -> set[str] | None:
    """
    Return contexts to build, or None if everything should rebuild.
    """
    affected: set[str] = set()
    for raw in changed_files:
        path = normalize_changed_path(raw)
        if not path:
            continue
        if (
            path == "entrypoint.sh"
            or path.startswith("ci/")
            or path.startswith(".github/")
        ):
            return None
        top = path.split("/")[0]
        if top in contexts:
            affected.add(top)
    return affected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root (default: current directory)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Build all discovered contexts",
    )
    parser.add_argument(
        "--changed-list",
        type=Path,
        default=None,
        help="File with one changed path per line (git diff-style paths)",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    registry = load_registry(repo_root)
    all_contexts = discover_contexts(repo_root)
    if not all_contexts:
        out = {"include": [], "should_run": False}
        print(json.dumps(out))
        return 0

    ctx_set = set(all_contexts)
    changed: list[str] = []
    if args.changed_list and args.changed_list.is_file():
        changed = args.changed_list.read_text(encoding="utf-8").splitlines()

    if args.full:
        to_build = set(all_contexts)
    else:
        aff = expand_affected(ctx_set, changed)
        if aff is None:
            to_build = ctx_set
        else:
            to_build = aff

    rows: list[dict] = []
    for c in sorted(to_build):
        if c not in ctx_set:
            continue
        rows.extend(build_rows_for_context(repo_root, registry, c))

    out = {"include": rows, "should_run": bool(rows)}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
