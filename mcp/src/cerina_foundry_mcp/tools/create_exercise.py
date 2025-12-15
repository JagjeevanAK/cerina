"""Tool for creating CBT exercises via the multi-agent workflow."""

import asyncio
from typing import Any, Optional

from mcp.types import TextContent

from ..api.client import CerinaClient
from ..api.types import ReviewRequest
from ..config import settings


async def create_cbt_exercise(
    description: str,
    exercise_type_hint: Optional[str] = None,
    auto_approve: Optional[bool] = None,
) -> list[TextContent]:
    """
    Create a new CBT exercise using the multi-agent workflow.

    Args:
        description: Natural language description of the exercise to create.
        exercise_type_hint: Optional hint for exercise type
            (e.g., "exposure_hierarchy", "thought_record").
        auto_approve: Override default auto-approve setting.

    Returns:
        The created exercise or review-needed status.
    """
    client = CerinaClient()
    should_auto_approve = (
        auto_approve if auto_approve is not None else settings.auto_approve
    )

    try:
        session = await client.create_session(description, exercise_type_hint)
        session_id = str(session.session_id)

        for attempt in range(settings.max_poll_attempts):
            state = await client.get_session(session_id)

            if state.status == "error":
                return [
                    TextContent(
                        type="text",
                        text=f"Error creating exercise: Session failed.\n\nSession ID: {session_id}",
                    )
                ]

            if state.awaiting_human_input:
                if should_auto_approve:
                    # Auto-approve in MCP bypass mode
                    await client.submit_review(
                        session_id,
                        ReviewRequest(
                            decision="approve",
                            feedback="Auto-approved via MCP",
                            reviewer_id="mcp-auto",
                        ),
                    )
                else:
                    draft = await client.get_draft(session_id)
                    return [
                        TextContent(
                            type="text",
                            text=_format_review_needed(session_id, draft),
                        )
                    ]

            if state.workflow_stage in ("approved", "rejected"):
                if state.final_exercise:
                    return [
                        TextContent(
                            type="text",
                            text=_format_exercise(state.final_exercise),
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"Session {state.workflow_stage} but no exercise data available.\n\nSession ID: {session_id}",
                        )
                    ]

            await asyncio.sleep(settings.poll_interval)

        return [
            TextContent(
                type="text",
                text=f"Timeout waiting for exercise creation after {settings.max_poll_attempts * settings.poll_interval:.0f} seconds.\n\nSession ID: {session_id}\nYou can check status with get_session_status tool.",
            )
        ]

    finally:
        await client.close()


def _format_exercise(exercise: dict[str, Any]) -> str:
    """Format exercise as readable markdown text."""
    parts = [
        f"# {exercise.get('title', 'CBT Exercise')}",
        "",
        f"**Type:** {exercise.get('exercise_type', 'Unknown')}",
    ]

    if exercise.get("target_condition"):
        parts.append(f"**Target Condition:** {exercise['target_condition']}")

    parts.append("")

    if exercise.get("introduction"):
        parts.extend(["## Introduction", "", exercise["introduction"], ""])

    if exercise.get("steps"):
        parts.append("## Steps")
        parts.append("")
        for i, step in enumerate(exercise["steps"], 1):
            step_text = f"{i}. {step.get('description', '')}"
            parts.append(step_text)
            if step.get("anxiety_rating") is not None:
                rating = step["anxiety_rating"]
                parts.append(f"   - SUDS Anxiety Level: {rating}/100")
            if step.get("duration_minutes"):
                parts.append(f"   - Duration: {step['duration_minutes']} minutes")
            elif step.get("duration"):
                parts.append(f"   - Duration: {step['duration']}")
            if step.get("coping_strategies"):
                parts.append(f"   - Coping Strategies: {', '.join(step['coping_strategies'])}")
        parts.append("")

    if exercise.get("safety_notes"):
        parts.append("## Safety Notes")
        parts.append("")
        for note in exercise["safety_notes"]:
            parts.append(f"- {note}")
        parts.append("")

    if exercise.get("contraindications"):
        parts.append("## Contraindications")
        parts.append("")
        for ci in exercise["contraindications"]:
            parts.append(f"- {ci}")
        parts.append("")

    if exercise.get("therapist_notes"):
        parts.extend(["## Therapist Notes", "", exercise["therapist_notes"], ""])

    if exercise.get("evidence_base"):
        parts.extend(["## Evidence Base", "", exercise["evidence_base"], ""])

    return "\n".join(parts)


def _format_review_needed(session_id: str, draft: Any) -> str:
    """Format review-needed response."""
    return f"""# Human Review Required

The CBT exercise has been drafted and requires human review before approval.

**Session ID:** `{session_id}`
**Draft Version:** {draft.draft_version}
**Iterations:** {draft.iteration_count}
**Safety Score:** {draft.safety_score if draft.safety_score else 'N/A'}
**Empathy Score:** {draft.empathy_score if draft.empathy_score else 'N/A'}

## Draft Preview

{draft.current_draft[:2000] if draft.current_draft else 'No draft content available'}

---

To approve this exercise, use the `approve_exercise` tool with session_id="{session_id}"

Or open the React Dashboard to review and edit the draft interactively."""
