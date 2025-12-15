"""Session API endpoints."""

import asyncio
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...schemas.session import (
    CreateSessionRequest,
    SessionResponse,
    SessionStateResponse,
    SessionListResponse,
    QualityMetricsResponse,
    ScratchpadSummary,
)
from ...schemas.review import ReviewRequest, ReviewResponse, DraftForReviewResponse
from ...services.session_service import SessionService
from ...services.graph_service import GraphService
from ...services.streaming_service import StreamingService
from ..deps import get_session_service, get_graph_service, get_streaming_service

router = APIRouter()


async def run_workflow_background(
    graph_service: GraphService,
    session_service: SessionService,
    user_input: str,
    thread_id: str,
    session_id: UUID,
):
    """Run the workflow in the background."""
    import traceback
    import structlog
    logger = structlog.get_logger(__name__)
    
    try:
        result = await graph_service.start_session(
            user_input=user_input,
            thread_id=thread_id,
        )
        # Update session with final state
        await session_service.update_session_from_state(thread_id, result)
    except Exception as e:
        logger.error("session_workflow_error", error=str(e), traceback=traceback.format_exc())
        await session_service.update_session(
            session_id,
            status="error",
        )


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    session_service: SessionService = Depends(get_session_service),
    graph_service: GraphService = Depends(get_graph_service),
):
    """
    Create a new CBT exercise generation session.

    This initializes the LangGraph workflow and creates a new thread.
    The graph begins execution in the background immediately.
    """
    thread_id = str(uuid4())

    # Create database record
    db_session = await session_service.create_session(
        thread_id=thread_id,
        raw_input=request.user_input,
    )

    # Start the workflow in background (non-blocking)
    background_tasks.add_task(
        run_workflow_background,
        graph_service,
        session_service,
        request.user_input,
        thread_id,
        db_session.id,
    )

    return SessionResponse(
        session_id=db_session.id,
        thread_id=db_session.thread_id,
        status=db_session.status,
        workflow_stage=db_session.workflow_stage,
        current_agent=None,
        iteration_count=db_session.iteration_count,
        created_at=db_session.created_at,
        updated_at=db_session.updated_at,
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_service: SessionService = Depends(get_session_service),
):
    """List all sessions with optional filtering."""
    sessions, total = await session_service.list_sessions(
        status=status,
        limit=limit,
        offset=offset,
    )

    return SessionListResponse(
        sessions=[
            SessionResponse(
                session_id=s.id,
                thread_id=s.thread_id,
                status=s.status,
                workflow_stage=s.workflow_stage,
                current_agent=None,
                iteration_count=s.iteration_count,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session(
    session_id: UUID,
    session_service: SessionService = Depends(get_session_service),
    graph_service: GraphService = Depends(get_graph_service),
):
    """Get full session details including current blackboard state."""
    db_session = await session_service.get_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = await graph_service.get_state(db_session.thread_id)

    quality_metrics = QualityMetricsResponse(
        safety_score=None,
        safety_passed=None,
        empathy_score=None,
        empathy_passed=None,
        converged=False,
    )

    scratchpad_summary = []

    if state:
        qm = state.get("quality_metrics", {})
        safety = qm.get("safety", {})
        empathy = qm.get("empathy", {})

        quality_metrics = QualityMetricsResponse(
            safety_score=safety.get("overall_safety_score"),
            safety_passed=safety.get("passed"),
            empathy_score=empathy.get("overall_empathy_score"),
            empathy_passed=empathy.get("passed"),
            converged=qm.get("converged", False),
        )

        # Build scratchpad summary
        for agent_id, scratchpad in state.get("scratchpads", {}).items():
            notes = scratchpad.get("notes", [])
            unresolved = [n for n in notes if not n.get("resolved", False)]
            scratchpad_summary.append(
                ScratchpadSummary(
                    agent_id=agent_id,
                    total_notes=len(notes),
                    unresolved_notes=len(unresolved),
                    last_action=scratchpad.get("last_action"),
                    critical_flags=sum(
                        1 for n in unresolved if n.get("severity") == "critical"
                    ),
                    major_flags=sum(
                        1 for n in unresolved if n.get("severity") == "major"
                    ),
                )
            )

    draft_version = 0
    if db_session.drafts:
        draft_version = max(d.version_number for d in db_session.drafts)

    return SessionStateResponse(
        session_id=db_session.id,
        thread_id=db_session.thread_id,
        status=db_session.status,
        workflow_stage=db_session.workflow_stage,
        current_draft=db_session.current_draft,
        draft_version=draft_version,
        quality_metrics=quality_metrics,
        scratchpad_summary=scratchpad_summary,
        awaiting_human_input=db_session.status == "awaiting_review",
        final_exercise=state.get("final_exercise") if state else None,
        iteration_count=db_session.iteration_count,
        created_at=db_session.created_at,
        updated_at=db_session.updated_at,
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
    session_service: SessionService = Depends(get_session_service),
):
    """Cancel and delete a session."""
    deleted = await session_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/review", response_model=ReviewResponse)
async def submit_review(
    session_id: UUID,
    review: ReviewRequest,
    session_service: SessionService = Depends(get_session_service),
    graph_service: GraphService = Depends(get_graph_service),
):
    """
    Submit human review decision.

    - approve: Finalizes the exercise and saves to database
    - reject: Marks session as rejected with feedback
    - edit: Updates draft with edits and resumes for re-review
    """
    db_session = await session_service.get_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if db_session.status != "awaiting_review":
        raise HTTPException(
            status_code=400,
            detail="Session is not awaiting review",
        )

    # Record the review
    await session_service.add_review(
        session_id=session_id,
        decision=review.decision,
        reviewer_id=review.reviewer_id,
        edits=review.edits,
        feedback=review.feedback,
    )

    # Resume the workflow
    result = await graph_service.resume_session(
        thread_id=db_session.thread_id,
        decision=review.decision,
        edits=review.edits,
        feedback=review.feedback,
        reviewer_id=review.reviewer_id,
    )

    # Update session from result
    await session_service.update_session_from_state(db_session.thread_id, result)

    # If approved, save the exercise
    if review.decision == "approve" and result.get("final_exercise"):
        await session_service.save_exercise(
            session_id=session_id,
            exercise_data=result["final_exercise"],
            approved_by=review.reviewer_id,
        )

    db_session = await session_service.get_session(session_id)

    return ReviewResponse(
        session_id=db_session.id,
        thread_id=db_session.thread_id,
        decision=review.decision,
        workflow_stage=db_session.workflow_stage or "unknown",
        reviewed_at=db_session.updated_at or db_session.created_at,
    )


@router.get("/{session_id}/draft", response_model=DraftForReviewResponse)
async def get_current_draft(
    session_id: UUID,
    session_service: SessionService = Depends(get_session_service),
    graph_service: GraphService = Depends(get_graph_service),
):
    """
    Get the current draft for human review.

    Returns the draft content along with all agent notes
    and quality scores.
    """
    db_session = await session_service.get_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = await graph_service.get_state(db_session.thread_id)

    draft_version = 0
    if db_session.drafts:
        draft_version = max(d.version_number for d in db_session.drafts)

    # Gather agent notes
    agent_notes = []
    if state:
        for agent_id, scratchpad in state.get("scratchpads", {}).items():
            for note in scratchpad.get("notes", []):
                agent_notes.append({
                    "agent_id": agent_id,
                    "note_type": note.get("note_type"),
                    "severity": note.get("severity"),
                    "content": note.get("content"),
                    "resolved": note.get("resolved", False),
                })

    qm = state.get("quality_metrics", {}) if state else {}
    safety = qm.get("safety", {})
    empathy = qm.get("empathy", {})

    return DraftForReviewResponse(
        session_id=db_session.id,
        thread_id=db_session.thread_id,
        current_draft=db_session.current_draft,
        draft_version=draft_version,
        final_exercise=state.get("final_exercise") if state else None,
        safety_score=safety.get("overall_safety_score"),
        empathy_score=empathy.get("overall_empathy_score"),
        iteration_count=db_session.iteration_count,
        agent_notes=agent_notes,
    )


@router.get("/{session_id}/stream")
async def stream_session(
    session_id: UUID,
    session_service: SessionService = Depends(get_session_service),
    streaming_service: StreamingService = Depends(get_streaming_service),
):
    """
    Server-Sent Events stream for real-time agent activity.

    Events include:
    - agent_started: An agent begins processing
    - agent_completed: An agent finishes
    - stage_changed: Workflow stage transition
    - human_review_needed: Draft ready for review
    - completed: Workflow finished
    - error: Error occurred
    """
    db_session = await session_service.get_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return StreamingResponse(
        streaming_service.stream_state_updates(db_session.thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
