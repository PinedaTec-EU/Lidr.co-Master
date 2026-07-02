from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass


@dataclass
class IdempotencyRecord:
    request_hash: str
    payload_json: str
    expires_at: float


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    def _purge_expired(self, *, now: float) -> None:
        expired_keys = [key for key, record in self._records.items() if record.expires_at <= now]
        for key in expired_keys:
            self._records.pop(key, None)

    def get(self, *, key: str, request_hash: str, now: float) -> str | None:
        self._purge_expired(now=now)
        record = self._records.get(key)
        if record is None:
            return None
        if record.request_hash != request_hash:
            raise ValueError("Idempotency key already used with a different request payload.")
        return record.payload_json

    def set(self, *, key: str, request_hash: str, payload: dict, ttl_seconds: int, now: float) -> None:
        self._purge_expired(now=now)
        self._records[key] = IdempotencyRecord(
            request_hash=request_hash,
            payload_json=json.dumps(payload, ensure_ascii=True, sort_keys=True),
            expires_at=now + ttl_seconds,
        )


def build_request_hash(*, transcript: str) -> str:
    return hashlib.sha256(transcript.encode("utf-8")).hexdigest()


idempotency_store = InMemoryIdempotencyStore()
