"""Supervisor agent for orchestrating the CBT clinical review workflow."""

from typing import Any, Literal

from src.agents.config.prompts import SUPERVISOR_PROMPT
from src.agents.state.graph_state import GraphState
from src.agents.agents.base import BaseAgent


class SupervisorAgent(BaseAgent):
    """Agent responsible for orchestrating the multi-agent workflow."""

    agent_id: str = "supervisor"
    description: str = "Orchestrates the CBT clinical review workflow and routes tasks to specialists"

    def get_system_prompt(self, state: GraphState) -> str:
        """Get the system prompt for the supervisor."""
        quality_metrics = state.get("quality_metrics", {})
        safety = quality_metrics.get("safety", {})
        empathy = quality_metrics.get("empathy", {})

        return SUPERVISOR_PROMPT.format(
            max_iterations=quality_metrics.get("max_iterations", 5),
            workflow_stage=state.get("workflow_stage", "initializing"),
            iteration_count=state.get("iteration_count", 0),
            safety_passed=safety.get("passed", False),
            empathy_passed=empathy.get("passed", False),
        )

    async def process(self, state: GraphState) -> dict[str, Any]:
        """Determine the next step in the workflow."""
        # Get routing decision
        next_agent = self.route(state)

        # Update scratchpad
        scratchpad = self._get_scratchpad(state)
        scratchpad["last_action"] = f"routed_to_{next_agent}"
        self._add_note(
            scratchpad,
            note_type="info",
            content=f"Routing decision: {next_agent}",
            severity="info",
        )

        return {
            "scratchpads": {self.agent_id: scratchpad},
            "current_agent": next_agent,
        }

    def route(
        self, state: GraphState
    ) -> Literal[
        "draftsman",
        "safety_guardian",
        "clinical_critic",
        "finalizer",
        "human_review",
        "end",
    ]:
        """
        Determine the next agent based on current state.

        This implements the routing logic for the supervisor-worker pattern.
        """
        stage = state.get("workflow_stage", "initializing")
        quality_metrics = state.get("quality_metrics", {})
        iteration = state.get("iteration_count", 0)
        max_iterations = quality_metrics.get("max_iterations", 5)

        safety = quality_metrics.get("safety", {})
        empathy = quality_metrics.get("empathy", {})

        # Initial state - start with drafting
        if stage == "initializing":
            return "draftsman"

        # After drafting - go to safety review
        elif stage == "drafting":
            return "safety_guardian"

        # After safety review
        elif stage == "safety_review":
            if not safety.get("passed", False):
                # Safety failed - need revision
                if iteration >= max_iterations:
                    # Max iterations reached - force human review
                    return "human_review"
                return "draftsman"
            # Safety passed - go to clinical review
            return "clinical_critic"

        # After clinical review
        elif stage == "clinical_review":
            if not empathy.get("passed", False):
                # Empathy failed - need revision
                if iteration >= max_iterations:
                    return "human_review"
                return "draftsman"
            # Both passed - go to finalization
            return "finalizer"

        # Revision stage - route back to appropriate reviewer
        elif stage == "revising":
            # After revision, go back to safety review
            return "safety_guardian"

        # After finalization - human review
        elif stage == "finalizing":
            return "human_review"

        # Terminal states
        elif stage in ["approved", "rejected"]:
            return "end"

        # Human review stage - wait for human input
        elif stage == "human_review":
            human_review = state.get("human_review", {})
            decision = human_review.get("decision")

            if decision == "approve":
                return "end"
            elif decision == "reject":
                return "end"
            elif decision == "edit":
                # Human made edits - re-run safety review
                return "safety_guardian"
            else:
                # Still waiting for human input
                return "human_review"

        # Default - go to human review for safety
        return "human_review"

    def should_continue(self, state: GraphState) -> bool:
        """Check if the workflow should continue or end."""
        stage = state.get("workflow_stage", "initializing")

        # End conditions
        if stage in ["approved", "rejected", "end"]:
            return False

        # Check if awaiting human input
        if state.get("awaiting_human_input", False):
            return False

        return True

    def get_routing_summary(self, state: GraphState) -> dict:
        """Get a summary of the current routing state for debugging."""
        quality_metrics = state.get("quality_metrics", {})
        safety = quality_metrics.get("safety", {})
        empathy = quality_metrics.get("empathy", {})

        return {
            "current_stage": state.get("workflow_stage"),
            "current_agent": state.get("current_agent"),
            "iteration_count": state.get("iteration_count"),
            "safety_passed": safety.get("passed"),
            "safety_score": safety.get("overall_safety_score"),
            "empathy_passed": empathy.get("passed"),
            "empathy_score": empathy.get("overall_empathy_score"),
            "converged": quality_metrics.get("converged"),
            "awaiting_human": state.get("awaiting_human_input"),
            "next_route": self.route(state),
        }
