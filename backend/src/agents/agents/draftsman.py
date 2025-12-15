"""Draftsman agent for creating and revising CBT exercises."""

from typing import Any

from src.agents.config.prompts import DRAFTSMAN_PROMPT
from src.agents.state.graph_state import GraphState
from src.agents.agents.base import BaseAgent


class DraftsmanAgent(BaseAgent):
    """Agent responsible for creating and revising CBT exercise content."""

    agent_id: str = "draftsman"
    description: str = "Creates and revises CBT exercises based on user requests and feedback"

    def get_system_prompt(self, state: GraphState) -> str:
        """Get the system prompt for the draftsman."""
        # Gather feedback from other agents
        feedback_parts = []
        scratchpads = state.get("scratchpads", {})

        for agent_id, scratchpad in scratchpads.items():
            if agent_id in ["safety_guardian", "clinical_critic"]:
                notes = scratchpad.get("notes", [])
                unresolved = [n for n in notes if not n.get("resolved", False)]
                if unresolved:
                    feedback_parts.append(f"\n### Feedback from {agent_id}:")
                    for note in unresolved:
                        severity = note.get("severity", "info")
                        content = note.get("content", "")
                        line_ref = note.get("line_reference")
                        line_info = f" (line {line_ref})" if line_ref else ""
                        feedback_parts.append(f"- [{severity}]{line_info}: {content}")

        feedback = "\n".join(feedback_parts) if feedback_parts else "No previous feedback."

        # Determine task description
        user_request = state.get("user_request", {})
        raw_input = user_request.get("raw_input", "")
        current_draft = state.get("current_draft", "")
        iteration = state.get("iteration_count", 0)

        if iteration == 0 or not current_draft:
            task_description = f"Create an initial CBT exercise for: {raw_input}"
        else:
            task_description = f"""Revise the current draft based on feedback.

## Current Draft (Version {state.get('draft_history', {}).get('current_version', 0)}):
{current_draft}

## Original Request:
{raw_input}"""

        return DRAFTSMAN_PROMPT.format(
            task_description=task_description,
            feedback=feedback,
        )

    async def process(self, state: GraphState) -> dict[str, Any]:
        """Create or revise the CBT exercise draft."""
        system_prompt = self.get_system_prompt(state)

        # Create user message based on context
        user_request = state.get("user_request", {})
        raw_input = user_request.get("raw_input", "")
        iteration = state.get("iteration_count", 0)

        if iteration == 0:
            user_message = f"Please create a CBT exercise for: {raw_input}"
        else:
            user_message = "Please revise the draft based on the feedback provided."

        # Get response from LLM
        response = await self.chat(system_prompt, user_message)

        # Update scratchpad
        scratchpad = self._get_scratchpad(state)
        scratchpad["last_action"] = "draft_created" if iteration == 0 else "draft_revised"
        self._add_note(
            scratchpad,
            note_type="info",
            content=f"{'Created initial' if iteration == 0 else 'Revised'} draft (iteration {iteration + 1})",
            severity="info",
        )

        # Update draft history
        draft_history = state.get("draft_history", {"current_version": 0, "versions": []})
        new_version = draft_history["current_version"] + 1
        draft_history["current_version"] = new_version
        draft_history["versions"].append({
            "version_number": new_version,
            "content": response,
            "created_at": self._get_timestamp(),
            "created_by": self.agent_id,
            "revision_notes": f"Iteration {iteration + 1}",
        })

        # Parse intent from first draft
        user_request_update = state.get("user_request", {}).copy()
        if iteration == 0:
            user_request_update["intent"] = self._parse_intent(raw_input)
            user_request_update["exercise_type"] = self._detect_exercise_type(raw_input)
            user_request_update["target_condition"] = self._extract_condition(raw_input)

        return {
            "current_draft": response,
            "draft_history": draft_history,
            "scratchpads": {self.agent_id: scratchpad},
            "workflow_stage": "drafting", 
            "user_request": user_request_update,
            "iteration_count": iteration + 1,
        }

    def _parse_intent(self, raw_input: str) -> str:
        """Parse the user's intent from their input."""
        raw_lower = raw_input.lower()
        if "exposure" in raw_lower or "hierarchy" in raw_lower:
            return "create_exposure_hierarchy"
        elif "thought record" in raw_lower:
            return "create_thought_record"
        elif "behavioral activation" in raw_lower or "activity" in raw_lower:
            return "create_behavioral_activation"
        elif "relaxation" in raw_lower or "breathing" in raw_lower:
            return "create_relaxation_technique"
        elif "cognitive restructur" in raw_lower:
            return "create_cognitive_restructuring"
        return "create_cbt_exercise"

    def _detect_exercise_type(self, raw_input: str) -> str:
        """Detect the exercise type from user input."""
        raw_lower = raw_input.lower()
        if "exposure" in raw_lower or "hierarchy" in raw_lower:
            return "exposure_hierarchy"
        elif "thought record" in raw_lower:
            return "thought_record"
        elif "behavioral activation" in raw_lower:
            return "behavioral_activation"
        elif "relaxation" in raw_lower or "breathing" in raw_lower:
            return "relaxation_technique"
        elif "cognitive restructur" in raw_lower:
            return "cognitive_restructuring"
        return "other"

    def _extract_condition(self, raw_input: str) -> str:
        """Extract the target condition from user input."""
        raw_lower = raw_input.lower()
        conditions = [
            "agoraphobia",
            "social anxiety",
            "panic disorder",
            "generalized anxiety",
            "ocd",
            "ptsd",
            "depression",
            "phobia",
            "health anxiety",
            "separation anxiety",
        ]
        for condition in conditions:
            if condition in raw_lower:
                return condition.title()
        # Try to extract from "for X" pattern
        if " for " in raw_lower:
            after_for = raw_lower.split(" for ")[-1]
            # Take first few words as condition
            return after_for.split(".")[0].strip().title()
        return "Anxiety"  # Default
