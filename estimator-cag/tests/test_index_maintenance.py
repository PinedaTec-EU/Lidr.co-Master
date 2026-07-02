from __future__ import annotations

from app.embedding_pipeline.index_maintenance import (
    MANAGED_INDEX_PREFIX,
    index_matches,
    managed_metadata_indexes,
    normalize_indexdef,
)


def test_managed_metadata_indexes_cover_current_filterable_fields() -> None:
    names = {item.name for item in managed_metadata_indexes()}

    assert names == {
        f"{MANAGED_INDEX_PREFIX}client_sector",
        f"{MANAGED_INDEX_PREFIX}main_technology",
        f"{MANAGED_INDEX_PREFIX}year",
        f"{MANAGED_INDEX_PREFIX}complexity",
    }


def test_normalize_indexdef_collapses_whitespace_for_stable_comparison() -> None:
    raw = "CREATE   INDEX foo   ON chunks\n((metadata->>'client_sector'))"

    assert normalize_indexdef(raw) == "create index foo on chunks ((metadata->>'client_sector'))"


def test_index_matches_tolerates_postgres_rendering_differences() -> None:
    index = next(item for item in managed_metadata_indexes() if item.name.endswith("year"))
    current = (
        "CREATE INDEX ix_chunks_metadata_expr__year ON public.chunks "
        "USING btree ((((metadata ->> 'year'::text))::integer))"
    )

    assert index_matches(current, index) is True
