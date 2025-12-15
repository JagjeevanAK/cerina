"""HTTP client for Cerina Foundry backend."""

from typing import Optional

import httpx

from ..config import settings
from .types import (
    SessionResponse,
    SessionStateResponse,
    DraftForReviewResponse,
    ReviewRequest,
    ReviewResponse,
    ExerciseListResponse,
)


class CerinaClient:
    """Async HTTP client for the Cerina Foundry backend API."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.backend_url
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=30.0))
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def create_session(
        self,
        user_input: str,
        exercise_type_hint: Optional[str] = None,
    ) -> SessionResponse:
        """Create a new CBT exercise session."""
        client = await self._get_client()
        payload = {"user_input": user_input}
        if exercise_type_hint:
            payload["exercise_type_hint"] = exercise_type_hint

        response = await client.post(
            f"{self.base_url}/sessions",
            json=payload,
        )
        response.raise_for_status()
        return SessionResponse(**response.json())

    async def get_session(self, session_id: str) -> SessionStateResponse:
        """Get full session state."""
        client = await self._get_client()
        response = await client.get(f"{self.base_url}/sessions/{session_id}")
        response.raise_for_status()
        return SessionStateResponse(**response.json())

    async def get_draft(self, session_id: str) -> DraftForReviewResponse:
        """Get draft for review."""
        client = await self._get_client()
        response = await client.get(f"{self.base_url}/sessions/{session_id}/draft")
        response.raise_for_status()
        return DraftForReviewResponse(**response.json())

    async def submit_review(
        self,
        session_id: str,
        review: ReviewRequest,
    ) -> ReviewResponse:
        """Submit human review decision."""
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/sessions/{session_id}/review",
            json=review.model_dump(),
        )
        response.raise_for_status()
        return ReviewResponse(**response.json())

    async def list_exercises(
        self,
        exercise_type: Optional[str] = None,
        target_condition: Optional[str] = None,
        limit: int = 20,
    ) -> ExerciseListResponse:
        """List approved exercises."""
        client = await self._get_client()
        params = {"limit": limit}
        if exercise_type:
            params["exercise_type"] = exercise_type
        if target_condition:
            params["target_condition"] = target_condition

        response = await client.get(
            f"{self.base_url}/exercises",
            params=params,
        )
        response.raise_for_status()
        return ExerciseListResponse(**response.json())
