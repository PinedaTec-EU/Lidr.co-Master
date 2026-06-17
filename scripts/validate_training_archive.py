#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "training-archive" / "ai-engineering-2026-04"
STAGING_DIR = ARCHIVE_ROOT / ".staging"
BUILD_SCRIPT_PATH = REPO_ROOT / "scripts" / "build_training_archive.py"


spec = importlib.util.spec_from_file_location("build_training_archive", BUILD_SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load build script from {BUILD_SCRIPT_PATH}")
build_training_archive = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = build_training_archive
spec.loader.exec_module(build_training_archive)


def normalize_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = value.lower()
    value = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"`+", " ", value)
    value = re.sub(r"[*_>#-]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def text_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\w+", normalize_text(value), flags=re.UNICODE)
        if len(token) >= 5 and not token.isdigit()
    }


def load_body_text(index_path: Path) -> str:
    content = index_path.read_text()
    parts = content.split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else content


def validate_record(staging_path: Path) -> tuple[bool, dict[str, object]]:
    payload = json.loads(staging_path.read_text())
    record = build_training_archive.SnapshotRecord(
        slug=payload["slug"],
        source_url=payload["source_url"],
        title=payload["title"],
        archived_at=payload["archived_at"],
        discovered_links=payload.get("discovered_links", []),
        group_hint=payload.get("group_hint"),
        snapshot=payload.get("snapshot"),
        article_html=payload.get("article_html"),
        title_html=payload.get("title_html"),
        imgs=payload.get("imgs"),
        iframes=payload.get("iframes"),
        text_preview=payload.get("text_preview"),
    )
    group = build_training_archive.classify_group(record)
    index_path = ARCHIVE_ROOT / group / record.slug / "index.md"
    result = {
        "slug": record.slug,
        "group": group,
        "index_path": str(index_path.relative_to(REPO_ROOT)),
    }
    if not index_path.exists():
        result["error"] = "missing index.md"
        return False, result

    body_text = load_body_text(index_path)
    markdown_tokens = text_tokens(body_text)
    preview_source = record.text_preview or record.snapshot or record.title
    preview_tokens = text_tokens(preview_source)
    shared_tokens = markdown_tokens & preview_tokens
    coverage = len(shared_tokens) / len(preview_tokens) if preview_tokens else 0.0
    markdown_recall = len(shared_tokens) / len(markdown_tokens) if markdown_tokens else 0.0

    result["preview_tokens"] = len(preview_tokens)
    result["markdown_tokens"] = len(markdown_tokens)
    result["shared_tokens"] = len(shared_tokens)
    result["coverage"] = round(coverage, 3)
    result["markdown_recall"] = round(markdown_recall, 3)

    if len(preview_tokens) < 25:
        passed = (
            len(body_text) >= 50
            and len(markdown_tokens) >= max(10, len(preview_tokens))
            and len(shared_tokens) >= max(8, len(preview_tokens) - 2)
            and coverage >= 0.8
        )
    else:
        passed = (
            len(body_text) >= 300
            and (
                (
                    len(markdown_tokens) >= 30
                    and len(shared_tokens) >= min(20, len(preview_tokens))
                    and coverage >= 0.2
                )
                or (
                    len(markdown_tokens) >= 35
                    and len(shared_tokens) >= 35
                    and markdown_recall >= 0.95
                )
            )
        )
    if not passed:
        result["error"] = "insufficient text preservation"
    return passed, result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate archived training markdown against staging snapshots.")
    parser.add_argument("slugs", nargs="*", help="Optional slugs to validate. Defaults to all staging records.")
    args = parser.parse_args()

    staging_paths = sorted(STAGING_DIR.glob("*.json"))
    if args.slugs:
        requested = set(args.slugs)
        staging_paths = [path for path in staging_paths if path.stem in requested]

    if not staging_paths:
        print("No staging records selected.", file=sys.stderr)
        return 1

    results: list[dict[str, object]] = []
    failures = 0
    for staging_path in staging_paths:
        passed, result = validate_record(staging_path)
        result["passed"] = passed
        results.append(result)
        if not passed:
            failures += 1

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
