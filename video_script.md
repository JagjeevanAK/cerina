# Cerina Protocol Foundry — Loom Script (≤ 5 minutes)

Audience: reviewer evaluating the “Agentic Architect” sprint.

Goal: In <5 mins show (1) React UI + live agent workflow + HITL pause/approve, (2) MCP demo from an MCP client, and (3) quick code walkthrough of state + Postgres checkpointer.

---

## Pre-flight (do before recording)

- Backend running: `docker-compose up -d` (DB) then `cd backend && uv run python -m src.main`
- Frontend running: `cd frontend && npm run dev`
- Open dashboard: `http://localhost:3000`
- (Optional) Open backend docs: `http://localhost:8000/docs` (only if debug enabled)
- Claude Desktop already configured with MCP server per [mcp/README.md](mcp/README.md)

Use a short prompt that tends to trigger at least one revision loop (so you can show “debate/refine”):
- “Create an exposure hierarchy for agoraphobia. Include 10 steps, SUDS 0–100, coping strategies, and safety notes. Avoid medical advice.”

---

## 0:00–0:20 — Hook + what you built

**On screen**: Dashboard home (sessions list) in browser.

**Say**:
- “This is Cerina Protocol Foundry: a LangGraph multi-agent workflow that drafts CBT exercises, runs safety + clinical quality gates, and then pauses for human approval. It persists every step to Postgres so it can resume after a crash.”

Callouts (one sentence each):
- “UI shows the black box in real time.”
- “Same workflow is callable via MCP, so Claude Desktop can trigger it.”

---

## 0:20–2:05 — React UI demo: agents + streaming + HITL

**On screen**: Click “New Session”. Paste the prompt. Create.

**Say**:
- “When I create a session, the backend starts a background LangGraph run. The frontend subscribes via SSE to show stage changes.”

**On screen**: Session detail page.
- Point to “Live” badge, Agent Pipeline, Event Log.

**Say (while it runs)**:
- “The workflow is a staged review board: Draftsman → Safety Guardian → Clinical Critic → Finalizer → Human Review.”
- “If safety or empathy fails thresholds, it loops back to Draftsman for revision; otherwise it advances.”

**On screen**: When it reaches human review, open Review panel.

**Say**:
- “Here’s the Human-in-the-Loop interrupt. The graph pauses and persists state; the UI fetches the draft plus quality metrics and agent notes.”

**On screen**:
- Scroll agent notes + quality scores.
- Click Edit, make a small change (e.g., soften tone, add ‘stop if overwhelmed’).

**Say**:
- “If I edit, the workflow resumes from the checkpoint and re-runs safety review on the edited content. If I approve, it saves the final exercise artifact.”

**On screen**: Approve.

---

## 2:05–3:05 — How streaming works (SSE) + API endpoints (quick)

**On screen**: Open the backend route file and highlight the stream endpoint.

Show:
- [backend/src/api/v1/sessions.py](backend/src/api/v1/sessions.py#L325-L366)

**Say**:
- “The UI connects to `GET /api/v1/sessions/{id}/stream`. We use Server-Sent Events because it’s one-way updates and simpler than websockets here.”
- “The backend’s streaming service polls the persisted graph state and emits events like `stage_changed`, `human_review_needed`, and `completed`.”

Optional quick peek:
- [backend/src/services/streaming_service.py](backend/src/services/streaming_service.py)

---

## 3:05–4:10 — Code walkthrough: state + interrupt + checkpointer

### State (“blackboard”)

**On screen**: Open GraphState definition.
- [backend/src/agents/state/graph_state.py](backend/src/agents/state/graph_state.py)

**Say**:
- “All agents communicate through a shared blackboard state. It’s not just messages: we track draft versions, per-agent scratchpads, quality metrics, workflow stage, iteration count, and the final structured exercise.”
- “Scratchpads use a reducer to merge updates safely across nodes.”

### Interrupt (HITL)

**On screen**: Open human review node.
- [backend/src/agents/graph/nodes.py](backend/src/agents/graph/nodes.py#L164-L260)

**Say**:
- “The key HITL mechanic is `interrupt(review_data)` — that pauses graph execution and checkpoints state. When the human approves/edits/rejects, the backend resumes using LangGraph `Command(resume=...)`.”

### Persistence (Postgres checkpointer)

**On screen**: Open checkpointer setup.
- [backend/src/agents/graph/checkpointer.py](backend/src/agents/graph/checkpointer.py)

**Say**:
- “Checkpointing is done with `AsyncPostgresSaver`. Setup is run using a dedicated autocommit connection so Postgres DDL like concurrent index creation doesn’t fail inside a transaction.”
- “Because state is persisted, server restarts don’t lose the workflow, and the UI can always re-fetch the current state.”

### Graph routing (quality gates + loops)

**On screen**: Open builder + edges.
- [backend/src/agents/graph/builder.py](backend/src/agents/graph/builder.py)
- [backend/src/agents/graph/edges.py](backend/src/agents/graph/edges.py)

**Say**:
- “Routing is conditional: after safety/clinical checks we either loop back to Draftsman or proceed. There’s also a max-iteration cap that escalates to human review to avoid infinite loops.”

---

## 4:10–4:55 — MCP demo (Claude Desktop)

**On screen**: Claude Desktop (or MCP Inspector) with Cerina MCP enabled.

**Say**:
- “Now the same workflow is exposed via MCP as tools. The MCP server runs over stdio and calls the same backend API under the hood.”

**On screen**: Use a prompt like:
- “Ask Cerina Foundry to create a sleep hygiene protocol for insomnia.”

**Say**:
- “The MCP tool creates a session via the API and polls status. By default it respects human review, but there’s an optional auto-approve mode for purely machine-to-machine flows.”

If you want a code flash:
- [mcp/src/cerina_foundry_mcp/server.py](mcp/src/cerina_foundry_mcp/server.py)
- [mcp/src/cerina_foundry_mcp/tools/create_exercise.py](mcp/src/cerina_foundry_mcp/tools/create_exercise.py)

---

## 4:55–5:00 — Close

**Say**:
- “That’s Cerina: multi-agent drafting + safety and empathy gates, persistent pause/resume with Postgres checkpointing, transparent streaming UI, and MCP interoperability.”

---

## Backup: if reviewers ask “where is what?”

- Frontend session detail UI: [frontend/app/(dashboard)/sessions/[id]/page.tsx](frontend/app/(dashboard)/sessions/[id]/page.tsx)
- SSE hook: [frontend/hooks/use-event-source.ts](frontend/hooks/use-event-source.ts)
- Session API: [backend/src/api/v1/sessions.py](backend/src/api/v1/sessions.py)
- Workflow + interrupt: [backend/src/agents/graph/nodes.py](backend/src/agents/graph/nodes.py)
- Graph compilation: [backend/src/agents/graph/builder.py](backend/src/agents/graph/builder.py)
- Routing thresholds/loops: [backend/src/agents/graph/edges.py](backend/src/agents/graph/edges.py)
- Checkpointer: [backend/src/agents/graph/checkpointer.py](backend/src/agents/graph/checkpointer.py)
- MCP config: [mcp/README.md](mcp/README.md)
