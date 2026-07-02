from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


def _require_api_key(expected_key: str, provided_key: str | None) -> str:
    if not expected_key:
        return provided_key or ""
    if provided_key is None or not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return provided_key


def require_retrieval_key(x_api_key: str | None = Header(default=None)) -> str:
    return _require_api_key(settings.retrieval_api_key, x_api_key)


def require_estimate_key(x_api_key: str | None = Header(default=None)) -> str:
    return _require_api_key(settings.estimate_api_key, x_api_key)
