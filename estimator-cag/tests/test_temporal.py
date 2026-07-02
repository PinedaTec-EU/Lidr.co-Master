from __future__ import annotations

from datetime import date

from app.embedding_pipeline.temporal import contextual_boost, temporal_weight


def test_temporal_weight_penalizes_older_documents() -> None:
    recent = temporal_weight(document_year=2025, now=date(2026, 7, 2), half_life_days=730)
    older = temporal_weight(document_year=2020, now=date(2026, 7, 2), half_life_days=730)

    assert recent > older


def test_contextual_boost_rewards_technology_and_sector_matches() -> None:
    boost = contextual_boost(
        query="Need a finance dashboard on ruby_on_rails",
        client_sector="finance",
        main_technology="ruby_on_rails",
    )

    assert boost > 1.0
