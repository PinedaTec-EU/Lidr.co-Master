#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "training-archive" / "ai-engineering-2026-04"
STAGING_DIR = ARCHIVE_ROOT / ".staging"


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
    record = json.loads(staging_path.read_text())
    group = record.get("group_hint") or "98-misc"
    if not record.get("group_hint"):
        text = f"{record.get('slug', '')} {record.get('title', '')}".lower()
        if any(
            marker in text
            for marker in (
                "arquitectura-rag",
                "fundamentos-de-rag",
                "diagnostico-arquitectonico-del-sistema-rag-actual",
                "del-cag-estatico-al-flujo-rag",
                "reformulacion-de-queries",
                "retrieval-que-no-es-solo-cosine",
                "augmentation-ensamblar-contexto",
                "la-capa-de-datos-como-servicio",
                "contenido-y-el-ejercicio-de-este-modulo-98724306",
                "sesion-9",
                "sesión 9",
            )
        ):
            group = "09-session"
    index_path = ARCHIVE_ROOT / group / record["slug"] / "index.md"
    result = {
        "slug": record["slug"],
        "group": group,
        "index_path": str(index_path.relative_to(REPO_ROOT)),
    }
    if not index_path.exists():
        result["error"] = "missing index.md"
        return False, result

    body_text = load_body_text(index_path)
    markdown_tokens = text_tokens(body_text)
    preview_tokens = text_tokens(record.get("text_preview") or "")
    shared_tokens = markdown_tokens & preview_tokens
    coverage = len(shared_tokens) / len(preview_tokens) if preview_tokens else 0.0

    result["preview_tokens"] = len(preview_tokens)
    result["markdown_tokens"] = len(markdown_tokens)
    result["shared_tokens"] = len(shared_tokens)
    result["coverage"] = round(coverage, 3)

    passed = (
        len(body_text) >= 300
        and len(markdown_tokens) >= 30
        and len(shared_tokens) >= 20
        and coverage >= 0.2
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
