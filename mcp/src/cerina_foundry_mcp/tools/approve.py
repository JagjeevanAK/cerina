"""Tool for approving pending CBT exercises."""

from typing import Optional

from mcp.types import TextContent

from ..api.client import CerinaClient
from ..api.types import ReviewRequest
from .create_exercise import _format_exercise


async def approve_exercise(
    session_id: str,
    feedback: Optional[str] = None,
) -> list[TextContent]:
    """
    Approve a CBT exercise that is awaiting human review.

    Args:
        session_id: The UUID of the session to approve.
        feedback: Optional feedback to include with approval.

    Returns:
        The approved exercise or error message.
    """
    client = CerinaClient()

    try:
        state = await client.get_session(session_id)

        if not state.awaiting_human_input:
            return [
                TextContent(
                    type="text",
                    text=f"Session `{session_id}` is not awaiting review.\n\n"
                    f"**Current Status:** {state.status}\n"
                    f"**Workflow Stage:** {state.workflow_stage}",
                )
            ]

        review = ReviewRequest(
            decision="approve",
            feedback=feedback or "Approved via MCP tool",
            reviewer_id="mcp-user",
        )

        await client.submit_review(session_id, review)

        final_state = await client.get_session(session_id)

        if final_state.final_exercise:
            return [
                TextContent(
                    type="text",
                    text=f"Exercise approved successfully!\n\n{_format_exercise(final_state.final_exercise)}",
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Exercise approved.\n\n"
                    f"**Final Stage:** {final_state.workflow_stage}",
                )
            ]

    finally:
        await client.close()
