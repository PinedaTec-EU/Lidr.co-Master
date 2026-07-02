from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


MANAGED_INDEX_PREFIX = "ix_chunks_metadata_expr__"


@dataclass(frozen=True)
class ManagedIndex:
    name: str
    ddl: str
    match_fragments: tuple[str, ...]


def managed_metadata_indexes() -> list[ManagedIndex]:
    return [
        ManagedIndex(
            name=f"{MANAGED_INDEX_PREFIX}client_sector",
            ddl=(
                f"CREATE INDEX {MANAGED_INDEX_PREFIX}client_sector "
                "ON chunks ((metadata->>'client_sector'))"
            ),
            match_fragments=("metadata", "client_sector", "chunks"),
        ),
        ManagedIndex(
            name=f"{MANAGED_INDEX_PREFIX}main_technology",
            ddl=(
                f"CREATE INDEX {MANAGED_INDEX_PREFIX}main_technology "
                "ON chunks ((metadata->>'main_technology'))"
            ),
            match_fragments=("metadata", "main_technology", "chunks"),
        ),
        ManagedIndex(
            name=f"{MANAGED_INDEX_PREFIX}year",
            ddl=(
                f"CREATE INDEX {MANAGED_INDEX_PREFIX}year "
                "ON chunks (((metadata->>'year')::integer))"
            ),
            match_fragments=("metadata", "year", "integer", "chunks"),
        ),
        ManagedIndex(
            name=f"{MANAGED_INDEX_PREFIX}complexity",
            ddl=(
                f"CREATE INDEX {MANAGED_INDEX_PREFIX}complexity "
                "ON chunks ((metadata->>'complexity'))"
            ),
            match_fragments=("metadata", "complexity", "chunks"),
        ),
    ]


def normalize_indexdef(indexdef: str) -> str:
    normalized = " ".join(indexdef.strip().split()).lower()
    return normalized.replace('"', "")


def index_matches(current_indexdef: str, expected: ManagedIndex) -> bool:
    normalized = normalize_indexdef(current_indexdef)
    return all(fragment.lower() in normalized for fragment in expected.match_fragments)


async def reconcile_managed_metadata_indexes(engine: AsyncEngine) -> None:
    expected = {item.name: item for item in managed_metadata_indexes()}

    async with engine.begin() as conn:
        chunks_table = await conn.scalar(text("SELECT to_regclass('public.chunks')"))
        if chunks_table is None:
            return

        result = await conn.execute(
            text(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = 'chunks'
                  AND indexname LIKE :prefix
                """
            ),
            {"prefix": f"{MANAGED_INDEX_PREFIX}%"},
        )
        current = {row.indexname: row.indexdef for row in result}

        extra_indexes = sorted(set(current) - set(expected))
        for name in extra_indexes:
            await conn.execute(text(f"DROP INDEX IF EXISTS {name}"))

        for item in managed_metadata_indexes():
            current_def = current.get(item.name)
            if current_def is not None and index_matches(current_def, item):
                continue
            if current_def is not None:
                await conn.execute(text(f"DROP INDEX IF EXISTS {item.name}"))
            await conn.execute(text(item.ddl))
