"""Tool for listing approved CBT exercises."""

from typing import Optional

from mcp.types import TextContent

from ..api.client import CerinaClient


async def list_exercises(
    exercise_type: Optional[str] = None,
    target_condition: Optional[str] = None,
    limit: int = 10,
) -> list[TextContent]:
    """
    List approved CBT exercises from the Cerina Foundry database.

    Args:
        exercise_type: Filter by exercise type (e.g., "exposure_hierarchy").
        target_condition: Filter by target condition (e.g., "anxiety", "depression").
        limit: Maximum number of exercises to return (default: 10).

    Returns:
        List of approved exercises.
    """
    client = CerinaClient()

    try:
        result = await client.list_exercises(
            exercise_type=exercise_type,
            target_condition=target_condition,
            limit=limit,
        )

        if not result.exercises:
            return [
                TextContent(
                    type="text",
                    text="No exercises found matching the criteria.",
                )
            ]

        lines = [f"# CBT Exercises ({result.total} total)", ""]

        for ex in result.exercises:
            lines.append(f"## {ex.title}")
            lines.append("")
            lines.append(f"- **ID:** `{ex.id}`")
            lines.append(f"- **Type:** {ex.exercise_type}")
            if ex.target_condition:
                lines.append(f"- **Condition:** {ex.target_condition}")
            lines.append(f"- **Created:** {ex.created_at.strftime('%Y-%m-%d')}")
            if ex.approved_by:
                lines.append(f"- **Approved By:** {ex.approved_by}")
            if ex.introduction:
                lines.append("")
                lines.append(f"_{ex.introduction[:200]}{'...' if len(ex.introduction) > 200 else ''}_")
            lines.append("")

        return [TextContent(type="text", text="\n".join(lines))]

    finally:
        await client.close()
