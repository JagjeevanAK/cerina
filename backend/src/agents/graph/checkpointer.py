"""PostgreSQL checkpointer setup for LangGraph persistence."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import psycopg
import structlog
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from src.agents.config.settings import Settings, get_settings

logger = structlog.get_logger(__name__)

_pool: AsyncConnectionPool | None = None
_setup_done: bool = False


async def _run_setup_with_dedicated_connection(settings: Settings) -> None:
    """
    Run checkpointer setup using a dedicated connection with autocommit.

    CREATE INDEX CONCURRENTLY requires a connection outside any transaction block.
    We use a separate connection (not from pool) with autocommit=True for this.
    """
    global _setup_done

    if _setup_done:
        return

    logger.info("checkpointer_setup_starting", note="Creating checkpoint tables with dedicated connection...")

    try:
        # Create a dedicated connection with autocommit for setup
        conn = await psycopg.AsyncConnection.connect(
            settings.database_url,
            autocommit=True,
            prepare_threshold=0,
            row_factory=dict_row,
        )
        logger.info("checkpointer_setup_connection_created")

        try:
            checkpointer = AsyncPostgresSaver(conn)
            await checkpointer.setup()
            _setup_done = True
            logger.info("checkpointer_tables_created")
        finally:
            await conn.close()
            logger.info("checkpointer_setup_connection_closed")

    except Exception as e:
        error_str = str(e).lower()
        # Tables might already exist from a previous run
        if "already exists" in error_str:
            logger.info("checkpointer_tables_already_exist")
            _setup_done = True
        else:
            logger.error("checkpointer_setup_error", error=str(e), error_type=type(e).__name__)
            raise


async def get_connection_pool(
    settings: Settings | None = None,
) -> AsyncConnectionPool:
    """Get or create the async connection pool."""
    global _pool

    if _pool is None:
        settings = settings or get_settings()

        # Run setup first with dedicated connection
        await _run_setup_with_dedicated_connection(settings)

        # Create pool for normal operations (autocommit + dict_row for checkpointer)
        _pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=2,
            max_size=10,
            open=False,
            kwargs={"autocommit": True, "row_factory": dict_row},
        )
        await _pool.open()
        logger.info("connection_pool_created", database_url=settings.database_url[:30] + "...")

    return _pool


async def close_connection_pool() -> None:
    """Close the connection pool."""
    global _pool, _setup_done
    if _pool is not None:
        await _pool.close()
        _pool = None
        _setup_done = False
        logger.info("connection_pool_closed")


async def get_checkpointer(
    settings: Settings | None = None,
) -> AsyncPostgresSaver:
    """
    Get a PostgreSQL checkpointer for LangGraph.

    This creates an async checkpointer that persists graph state
    to PostgreSQL, enabling crash recovery and state inspection.
    """
    # get_connection_pool handles setup with dedicated connection
    pool = await get_connection_pool(settings)

    checkpointer = AsyncPostgresSaver(pool)
    logger.info("checkpointer_initialized")
    return checkpointer


@asynccontextmanager
async def create_checkpointer(
    settings: Settings | None = None,
) -> AsyncGenerator[AsyncPostgresSaver, None]:
    """
    Context manager for checkpointer lifecycle.

    Usage:
        async with create_checkpointer() as checkpointer:
            graph = build_graph(checkpointer=checkpointer)
            result = await graph.ainvoke(...)
    """
    settings = settings or get_settings()

    # Run setup with dedicated connection first
    await _run_setup_with_dedicated_connection(settings)

    # Create pool for operations
    async with AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=1,
        max_size=5,
        kwargs={"autocommit": True, "row_factory": dict_row},
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        logger.info("checkpointer_context_created")
        try:
            yield checkpointer
        finally:
            logger.info("checkpointer_context_closed")
