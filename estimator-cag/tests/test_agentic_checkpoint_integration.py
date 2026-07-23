from __future__ import annotations

import asyncio
import os

import pytest


def test_postgres_checkpointer_initializes_when_configured() -> None:
    connection_string = os.getenv("AGENT_CHECKPOINT_DATABASE_URL")
    if not connection_string:
        pytest.skip("AGENT_CHECKPOINT_DATABASE_URL is required for PostgreSQL checkpoint integration tests.")

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    async def setup() -> None:
        async with AsyncPostgresSaver.from_conn_string(connection_string) as saver:
            await saver.setup()

    asyncio.run(setup())
