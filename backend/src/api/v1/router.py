"""Main API router."""

from fastapi import APIRouter

from .sessions import router as sessions_router
from .exercises import router as exercises_router

router = APIRouter()

router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
router.include_router(exercises_router, prefix="/exercises", tags=["exercises"])
