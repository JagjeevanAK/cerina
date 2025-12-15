"""Service for interacting with the LangGraph agent system."""

import os
from typing import Any, AsyncGenerator, Optional

import structlog

logger = structlog.get_logger(__name__)


class GraphService:
    """Service for managing LangGraph workflow execution."""

    def __init__(self, database_url: str):
        """
        Initialize the graph service.

        Args:
            database_url: PostgreSQL connection URL for checkpointing
        """
        self.database_url = database_url
        self._workflow = None

    async def _get_workflow(self):
        """Get or create the workflow instance."""
        if self._workflow is None:
            logger.info("workflow_init_start", database_url=self.database_url[:40] + "...")
            os.environ["DATABASE_URL"] = self.database_url

            from src.agents.graph.builder import CBTWorkflow
            from src.agents.graph.checkpointer import get_checkpointer

            logger.info("workflow_init_getting_checkpointer")
            checkpointer = await get_checkpointer()
            logger.info("workflow_init_checkpointer_ready")

            self._workflow = CBTWorkflow(checkpointer=checkpointer)
            logger.info("workflow_init_complete")

        return self._workflow

    async def start_session(
        self,
        user_input: str,
        thread_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Start a new CBT exercise generation session.

        Args:
            user_input: The user's request
            thread_id: Optional thread ID (generated if not provided)

        Returns:
            Initial state after starting the workflow
        """
        workflow = await self._get_workflow()

        logger.info(
            "starting_session",
            user_input=user_input[:100],
            thread_id=thread_id,
        )

        result = await workflow.start(user_input, thread_id)

        logger.info(
            "session_started",
            thread_id=result.get("thread_id"),
            workflow_stage=result.get("workflow_stage"),
        )

        return result

    async def resume_session(
        self,
        thread_id: str,
        decision: str,
        edits: Optional[str] = None,
        feedback: Optional[str] = None,
        reviewer_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Resume an interrupted session with human input.

        Args:
            thread_id: The thread ID of the session
            decision: "approve", "reject", or "edit"
            edits: Edited content (for "edit" decision)
            feedback: Optional feedback text
            reviewer_id: Optional reviewer identifier

        Returns:
            State after resumption
        """
        workflow = await self._get_workflow()

        human_decision = {
            "decision": decision,
            "edits": edits,
            "feedback": feedback,
            "reviewer_id": reviewer_id,
        }

        logger.info(
            "resuming_session",
            thread_id=thread_id,
            decision=decision,
        )

        result = await workflow.resume(thread_id, human_decision)

        logger.info(
            "session_resumed",
            thread_id=thread_id,
            workflow_stage=result.get("workflow_stage"),
        )

        return result

    async def get_state(self, thread_id: str) -> Optional[dict[str, Any]]:
        """
        Get the current state of a session.

        Args:
            thread_id: The thread ID to retrieve state for

        Returns:
            Current state or None if not found
        """
        workflow = await self._get_workflow()
        return await workflow.get_state(thread_id)

    async def stream_session(
        self,
        user_input: str,
        thread_id: Optional[str] = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream session events for real-time updates.

        Args:
            user_input: The user's request
            thread_id: Optional thread ID

        Yields:
            Workflow events as they occur
        """
        workflow = await self._get_workflow()

        async for event in workflow.stream(user_input, thread_id):
            yield self._transform_event(event)

    def _transform_event(self, event: dict) -> dict:
        """Transform LangGraph event to API-friendly format."""
        event_type = event.get("event", "unknown")

        if event_type == "on_chain_start":
            return {
                "type": "agent_started",
                "agent": event.get("name"),
                "timestamp": event.get("timestamp"),
            }
        elif event_type == "on_chain_end":
            return {
                "type": "agent_completed",
                "agent": event.get("name"),
                "output": event.get("output", {}),
            }
        elif event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            content = getattr(chunk, "content", "") if chunk else ""
            return {
                "type": "token",
                "content": content,
            }
        elif event_type == "on_chain_stream":
            return {
                "type": "state_update",
                "data": event.get("data", {}),
            }
        else:
            return {
                "type": event_type,
                "data": event.get("data", {}),
            }
