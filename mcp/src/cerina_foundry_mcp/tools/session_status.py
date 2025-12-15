"""Tool for checking session status."""

from mcp.types import TextContent

from ..api.client import CerinaClient


async def get_session_status(session_id: str) -> list[TextContent]:
    """
    Get the current status of a CBT exercise creation session.

    Args:
        session_id: The UUID of the session to check.

    Returns:
        Current session status and details.
    """
    client = CerinaClient()

    try:
        state = await client.get_session(session_id)

        lines = [
            f"# Session Status",
            "",
            f"**Session ID:** `{state.session_id}`",
            f"**Thread ID:** `{state.thread_id}`",
            "",
            f"**Status:** {state.status}",
            f"**Workflow Stage:** {state.workflow_stage or 'N/A'}",
            f"**Iteration Count:** {state.iteration_count}",
            f"**Draft Version:** {state.draft_version}",
            f"**Awaiting Human Input:** {'Yes' if state.awaiting_human_input else 'No'}",
            "",
        ]

        qm = state.quality_metrics
        lines.extend([
            "## Quality Metrics",
            "",
            f"- **Safety Score:** {qm.safety_score if qm.safety_score is not None else 'N/A'}"
            + (f" ({'Passed' if qm.safety_passed else 'Failed'})" if qm.safety_passed is not None else ""),
            f"- **Empathy Score:** {qm.empathy_score if qm.empathy_score is not None else 'N/A'}"
            + (f" ({'Passed' if qm.empathy_passed else 'Failed'})" if qm.empathy_passed is not None else ""),
            f"- **Converged:** {'Yes' if qm.converged else 'No'}",
            "",
        ])

        if state.scratchpad_summary:
            lines.append("## Agent Notes Summary")
            lines.append("")
            for sp in state.scratchpad_summary:
                lines.append(f"### {sp.agent_id}")
                lines.append(f"- Total Notes: {sp.total_notes}")
                lines.append(f"- Unresolved: {sp.unresolved_notes}")
                lines.append(f"- Critical Flags: {sp.critical_flags}")
                lines.append(f"- Major Flags: {sp.major_flags}")
                if sp.last_action:
                    lines.append(f"- Last Action: {sp.last_action}")
                lines.append("")

        if state.final_exercise:
            lines.extend([
                "## Final Exercise",
                "",
                f"**Title:** {state.final_exercise.get('title', 'Untitled')}",
                f"**Type:** {state.final_exercise.get('exercise_type', 'Unknown')}",
                "",
            ])

        lines.extend([
            "## Timestamps",
            "",
            f"- **Created:** {state.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        ])
        if state.updated_at:
            lines.append(f"- **Updated:** {state.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

        return [TextContent(type="text", text="\n".join(lines))]

    finally:
        await client.close()
