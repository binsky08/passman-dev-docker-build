#!/usr/bin/env python3
"""
Discover image build matrix for GitHub Actions: dev (and demo when present) images per context.

Reads ci/registry.json. Emits JSON with { "include": [...], "should_run": true|false } to stdout.

When SETUP_PASSMAN_BRANCH is a release (for example 2.6.4), each dev and demo
image also gets the tag <context>-passman-<version>. The unsuffixed context tag
and passman-dev:latest stay rolling.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEMO_STAGE = re.compile(r"(?m)^FROM\s+\S+\s+AS\s+demo\s*$")
PASSMAN_BRANCH = re.compile(
    r"""(?m)^ENV[ \t]+SETUP_PASSMAN_BRANCH=(?:"([^"]+)"|'([^']+)'|([^\s#]+))"""
)
PASSMAN_RELEASE = re.compile(r"^v?(\d+\.\d+\.\d+)$")
# Extra Hub tag kept when SETUP_PASSMAN_BRANCH moves to another release:
#   <context>-passman-<version>
PASSMAN_TAG_MARKER = "passman"


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


def passman_branch_from_text(text: str) -> str | None:
    match = PASSMAN_BRANCH.search(text.replace("\r\n", "\n"))
    if not match:
        return None
    raw = next(group for group in match.groups() if group is not None)
    return raw.strip()


def normalize_release(raw: str | None) -> str | None:
    if raw is None:
        return None
    match = PASSMAN_RELEASE.fullmatch(raw.strip())
    if not match:
        return None
    return match.group(1)


def passman_release_from_text(text: str) -> str | None:
    return normalize_release(passman_branch_from_text(text))


def passman_release(repo_root: Path, context: str) -> str | None:
    dockerfile = repo_root / context / "Dockerfile"
    text = dockerfile.read_text(encoding="utf-8", errors="replace")
    return passman_release_from_text(text)


def passman_tag(context: str, release: str) -> str:
    return f"{context}-{PASSMAN_TAG_MARKER}-{release}"


def context_tags(image: str, context: str, release: str | None) -> list[str]:
    tags = [f"{image}:{context}"]
    if release:
        tags.append(f"{image}:{passman_tag(context, release)}")
    return tags


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
    release = passman_release(repo_root, context)

    if multi:
        demo_image = image_name(registry, demo_repo)
        rows.append(
            {
                "context": context,
                "build_mode": "stage",
                "target": "demo",
                "tags": ",".join(context_tags(demo_image, context, release)),
            }
        )

    dev_targets = context_tags(dev_image, context, release)
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
    repo_root: Path,
    registry: dict,
    contexts: set[str],
    changed_files: list[str],
) -> set[str] | None:
    """
    Return contexts to build, or None if everything should rebuild.

    Full rebuild only when shared runtime inputs change (entrypoint.sh).
    ci/registry.json updates only rebuild dev_latest_context (for :latest tag).
    Other ci/ or .github/ changes do not rebuild images (use workflow_dispatch
    "rebuild all" when the pipeline itself needs a full republish).
    """
    affected: set[str] = set()
    for raw in changed_files:
        path = normalize_changed_path(raw)
        if not path:
            continue
        if path == "entrypoint.sh":
            return None
        if path == "ci/registry.json":
            latest = registry.get("dev_latest_context")
            if latest and latest in contexts:
                affected.add(latest)
            continue
        if path.startswith("ci/") or path.startswith(".github/"):
            continue
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
        aff = expand_affected(repo_root, registry, ctx_set, changed)
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
