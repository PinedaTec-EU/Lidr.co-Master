from __future__ import annotations

from datetime import date
from math import exp, log


def temporal_weight(*, document_year: int | None, now: date, half_life_days: int) -> float:
    if document_year is None:
        return 1.0
    try:
        document_date = date(document_year, 12, 31)
    except ValueError:
        return 1.0
    age_days = max((now - document_date).days, 0)
    decay_constant = log(2) / half_life_days
    return exp(-decay_constant * age_days)


def contextual_boost(*, query: str, client_sector: str | None, main_technology: str | None) -> float:
    lowered = query.lower()
    boost = 1.0
    if main_technology and main_technology.lower() in lowered:
        boost *= 1.15
    if client_sector and client_sector.lower() in lowered:
        boost *= 1.1
    return boost
