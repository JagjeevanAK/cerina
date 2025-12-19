# Cerina MCP Server

MCP (Model Context Protocol) server that exposes the CBT Clinical Review Multi-Agent System as tools for AI assistants like Claude Desktop.

Publish URL: https://pypi.org/project/cerina-mcp/
## Features

- **create_cbt_exercise**: Create CBT exercises using the multi-agent workflow
- **list_exercises**: List approved exercises from the database
- **get_session_status**: Check status of exercise creation sessions
- **approve_exercise**: Approve exercises awaiting human review

## Prerequisites

1. Python 3.13+
2. [uv](https://github.com/astral-sh/uv) package manager
3. Cerina Foundry backend running at `http://localhost:8000`

## Installation

```bash
cd mcp
uv sync
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

### Daily Use
```json
{
  "mcpServers": {
    "cerina-mcp": {
      "command": "uvx",
      "args": ["cerina-foundry"]
    }
  }
}
```

### Development
```json
{
  "mcpServers": {
    "cerina-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/jagjeevankashid/Developer/cerina/mcp",
        "run",
        "cerina-foundry"
      ],
      "env": {
        "CERINA_BACKEND_URL": "http://localhost:8000/api/v1",
      }
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CERINA_BACKEND_URL` | `http://localhost:8000/api/v1` | Backend API URL |
| `CERINA_AUTO_APPROVE` | `false` | Auto-approve without human review |
| `CERINA_POLL_INTERVAL` | `2.0` | Seconds between status polls |
| `CERINA_MAX_POLL_ATTEMPTS` | `300` | Max polls before timeout (~10 min) |

## Usage Examples

Once configured in Claude Desktop:

### Create an Exercise
> "Ask Cerina Foundry to create a sleep hygiene protocol for patients with insomnia"

### List Exercises
> "Show me the approved CBT exercises for anxiety"

### Check Status
> "What's the status of session abc123?"

### Approve Pending Exercise
> "Approve the exercise in session xyz789"

## Development

Run the server manually:

```bash
uv run cerina-foundry
```

Test with MCP inspector:

```bash
npx @modelcontextprotocol/inspector uv --directory . run cerina-foundry
```
