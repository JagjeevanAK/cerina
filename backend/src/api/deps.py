"""API dependencies."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..config.settings import Settings, get_settings
from ..services.session_service import SessionService
from ..services.graph_service import GraphService
from ..services.streaming_service import StreamingService


async def get_session_service(
    db: AsyncSession = Depends(get_db),
) -> SessionService:
    """Get session service dependency."""
    return SessionService(db)


def get_graph_service(
    settings: Settings = Depends(get_settings),
) -> GraphService:
    """Get graph service dependency."""
    return GraphService(settings.agents_database_url)


def get_streaming_service(
    graph_service: GraphService = Depends(get_graph_service),
) -> StreamingService:
    """Get streaming service dependency."""
    return StreamingService(graph_service)
