"""SSE streaming service for real-time updates."""

import asyncio
import json
from typing import Any, AsyncGenerator

import structlog

logger = structlog.get_logger(__name__)


class StreamingService:
    """Service for SSE streaming of agent activity."""

    def __init__(self, graph_service):
        """
        Initialize the streaming service.

        Args:
            graph_service: GraphService instance for workflow execution
        """
        self.graph_service = graph_service
        self._active_streams: dict[str, asyncio.Event] = {}

    async def stream_session(
        self,
        user_input: str,
        thread_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream SSE events for a new session.

        Args:
            user_input: The user's request
            thread_id: Optional thread ID

        Yields:
            SSE-formatted event strings
        """
        cancel_event = asyncio.Event()

        if thread_id:
            self._active_streams[thread_id] = cancel_event

        try:
            async for event in self.graph_service.stream_session(
                user_input, thread_id
            ):
                if cancel_event.is_set():
                    yield self._format_sse({"type": "cancelled"})
                    break

                yield self._format_sse(event)

            # Send completion event
            yield self._format_sse({"type": "complete"})

        except Exception as e:
            logger.error("stream_error", error=str(e))
            yield self._format_sse({
                "type": "error",
                "message": str(e),
                "recoverable": False,
            })
        finally:
            if thread_id and thread_id in self._active_streams:
                del self._active_streams[thread_id]

    async def stream_state_updates(
        self,
        thread_id: str,
        poll_interval: float = 1.0,
    ) -> AsyncGenerator[str, None]:
        """
        Stream state updates for an existing session.

        Args:
            thread_id: The thread ID to monitor
            poll_interval: Seconds between state checks

        Yields:
            SSE-formatted event strings with state updates
        """
        cancel_event = asyncio.Event()
        self._active_streams[thread_id] = cancel_event
        last_stage = None

        try:
            while not cancel_event.is_set():
                state = await self.graph_service.get_state(thread_id)

                if state is None:
                    yield self._format_sse({
                        "type": "error",
                        "message": "Session not found",
                    })
                    break

                current_stage = state.get("workflow_stage")

                # Send update if stage changed
                if current_stage != last_stage:
                    yield self._format_sse({
                        "type": "stage_changed",
                        "from_stage": last_stage,
                        "to_stage": current_stage,
                        "iteration_count": state.get("iteration_count"),
                    })
                    last_stage = current_stage

                # Check for terminal states
                if current_stage in ["approved", "rejected"]:
                    yield self._format_sse({
                        "type": "completed",
                        "final_stage": current_stage,
                        "final_exercise": state.get("final_exercise"),
                    })
                    break

                # Check for human review
                if state.get("awaiting_human_input"):
                    yield self._format_sse({
                        "type": "human_review_needed",
                        "draft_preview": state.get("current_draft", "")[:500],
                        "final_exercise": state.get("final_exercise"),
                    })
                    break

                await asyncio.sleep(poll_interval)

        except asyncio.CancelledError:
            yield self._format_sse({"type": "cancelled"})
        finally:
            if thread_id in self._active_streams:
                del self._active_streams[thread_id]

    def cancel_stream(self, thread_id: str) -> bool:
        """
        Cancel an active stream.

        Args:
            thread_id: The thread ID of the stream to cancel

        Returns:
            True if stream was cancelled, False if not found
        """
        if thread_id in self._active_streams:
            self._active_streams[thread_id].set()
            return True
        return False

    def _format_sse(self, data: dict[str, Any]) -> str:
        """Format data as an SSE event string."""
        return f"data: {json.dumps(data)}\n\n"
