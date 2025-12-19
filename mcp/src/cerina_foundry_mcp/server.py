"""MCP Server for Cerina - CBT Clinical Review System."""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools import (
    create_cbt_exercise,
    list_exercises,
    get_session_status,
    approve_exercise,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("cerina-foundry")

TOOLS = [
    Tool(
        name="create_cbt_exercise",
        description="""Create a new CBT (Cognitive Behavioral Therapy) exercise using Cerina Foundry's multi-agent system.

The system uses specialized AI agents to:
1. Draft the exercise content (Draftsman)
2. Review for safety concerns (Safety Guardian)
3. Evaluate clinical accuracy and empathy (Clinical Critic)
4. Format the final artifact (Finalizer)

IMPORTANT DISPLAY INSTRUCTIONS:
- When this tool returns an exercise, you MUST create an ARTIFACT to display the COMPLETE exercise content in the sidebar panel.
- Use artifact type "text/markdown" with a descriptive title like "CBT Exercise: [condition]"
- Include ALL steps with their descriptions, SUDS anxiety ratings (0-100), coping strategies, duration, safety notes, and contraindications.
- Do NOT summarize or truncate - show the FULL formatted exercise exactly as returned.
- The artifact allows users to easily copy, reference, and save the exercise.

By default, exercises require human approval via the React Dashboard. Set auto_approve=true to bypass review (use with caution).""",
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Natural language description of the CBT exercise to create. Be specific about the target condition, exercise type, and any special requirements. Example: 'Create an exposure hierarchy for social anxiety with 10 progressive steps starting from making eye contact to giving a presentation.'",
                },
                "exercise_type_hint": {
                    "type": "string",
                    "description": "Optional hint for exercise type. Examples: 'exposure_hierarchy', 'thought_record', 'behavioral_activation', 'cognitive_restructuring', 'relaxation_exercise'",
                },
                "auto_approve": {
                    "type": "boolean",
                    "description": "If true, automatically approve the exercise without human review. Default: false. Use with caution - human review ensures clinical safety.",
                },
            },
            "required": ["description"],
        },
    ),
    Tool(
        name="list_exercises",
        description="List approved CBT exercises from the Cerina Foundry database. Filter by type or target condition.",
        inputSchema={
            "type": "object",
            "properties": {
                "exercise_type": {
                    "type": "string",
                    "description": "Filter by exercise type (e.g., 'exposure_hierarchy', 'thought_record')",
                },
                "target_condition": {
                    "type": "string",
                    "description": "Filter by target condition (e.g., 'anxiety', 'depression', 'insomnia', 'phobia')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of exercises to return (default: 10, max: 50)",
                },
            },
        },
    ),
    Tool(
        name="get_session_status",
        description="Get the current status of a CBT exercise creation session. Use this to check progress or troubleshoot.",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The UUID of the session to check",
                },
            },
            "required": ["session_id"],
        },
    ),
    Tool(
        name="approve_exercise",
        description="Approve a CBT exercise that is awaiting human review. Use this when you've reviewed the draft (via get_session_status) and want to approve it.",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The UUID of the session to approve",
                },
                "feedback": {
                    "type": "string",
                    "description": "Optional feedback to include with approval",
                },
            },
            "required": ["session_id"],
        },
    ),
]


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return the list of available tools."""
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool invocations."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        if name == "create_cbt_exercise":
            return await create_cbt_exercise(
                description=arguments["description"],
                exercise_type_hint=arguments.get("exercise_type_hint"),
                auto_approve=arguments.get("auto_approve"),
            )
        elif name == "list_exercises":
            return await list_exercises(
                exercise_type=arguments.get("exercise_type"),
                target_condition=arguments.get("target_condition"),
                limit=arguments.get("limit", 10),
            )
        elif name == "get_session_status":
            return await get_session_status(
                session_id=arguments["session_id"],
            )
        elif name == "approve_exercise":
            return await approve_exercise(
                session_id=arguments["session_id"],
                feedback=arguments.get("feedback"),
            )
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown tool: {name}. Available tools: create_cbt_exercise, list_exercises, get_session_status, approve_exercise",
                )
            ]
    except Exception as e:
        logger.exception(f"Error in tool {name}")
        return [
            TextContent(
                type="text",
                text=f"Error executing {name}: {type(e).__name__}: {str(e)}",
            )
        ]


async def run_server():
    """Run the MCP server."""
    logger.info("Starting Cerina Foundry MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
