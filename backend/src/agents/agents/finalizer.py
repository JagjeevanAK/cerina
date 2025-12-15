"""Finalizer agent for formatting the final CBT exercise artifact."""

import json
import re
from typing import Any

from src.agents.config.prompts import FINALIZER_PROMPT
from src.agents.state.graph_state import GraphState
from src.agents.agents.base import BaseAgent


class FinalizerAgent(BaseAgent):
    """Agent responsible for finalizing and formatting CBT exercises."""

    agent_id: str = "finalizer"
    description: str = "Formats approved CBT exercises into structured artifacts"

    def get_system_prompt(self, state: GraphState) -> str:
        """Get the system prompt for the finalizer."""
        current_draft = state.get("current_draft", "")
        quality_metrics = state.get("quality_metrics", {})

        safety_score = quality_metrics.get("safety", {}).get("overall_safety_score", 0.0)
        empathy_score = quality_metrics.get("empathy", {}).get("overall_empathy_score", 0.0)

        return FINALIZER_PROMPT.format(
            current_draft=current_draft,
            safety_score=f"{safety_score:.2f}",
            empathy_score=f"{empathy_score:.2f}",
        )

    async def process(self, state: GraphState) -> dict[str, Any]:
        """Finalize the CBT exercise into a structured format."""
        system_prompt = self.get_system_prompt(state)

        user_message = """Please transform the draft into the final structured JSON format.
Ensure all required fields are present and the exercise is ready for human review.
Output ONLY the JSON object, no additional text."""

        response = await self.chat(system_prompt, user_message)

        # Parse the JSON response
        final_exercise = self._parse_exercise_json(response, state)

        # Update scratchpad
        scratchpad = self._get_scratchpad(state)
        scratchpad["last_action"] = "finalization_complete"
        self._add_note(
            scratchpad,
            note_type="info",
            content=f"Finalized exercise: {final_exercise.get('title', 'Untitled')}",
            severity="info",
        )

        return {
            "final_exercise": final_exercise,
            "scratchpads": {self.agent_id: scratchpad},
            "workflow_stage": "refinement", 
        }

    def _parse_exercise_json(self, response: str, state: GraphState) -> dict:
        """Parse the finalizer's JSON response into a structured exercise."""
        # Try to extract JSON from the response
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                exercise = json.loads(json_match.group())
                return self._validate_exercise(exercise, state)
            except json.JSONDecodeError:
                pass

        # Fallback: construct exercise from state
        return self._construct_exercise_from_state(state)

    def _validate_exercise(self, exercise: dict, state: GraphState) -> dict:
        """Validate and fill in missing fields of the exercise."""
        user_request = state.get("user_request", {})

        # Ensure required fields
        defaults = {
            "exercise_type": user_request.get("exercise_type", "other"),
            "title": "CBT Exercise",
            "target_condition": user_request.get("target_condition", "Anxiety"),
            "introduction": "",
            "steps": [],
            "safety_notes": [],
            "therapist_notes": None,
            "contraindications": [],
            "evidence_base": None,
        }

        for key, default in defaults.items():
            if key not in exercise or exercise[key] is None:
                exercise[key] = default

        # Validate steps
        if exercise.get("steps"):
            validated_steps = []
            for i, step in enumerate(exercise["steps"]):
                validated_step = {
                    "step_number": step.get("step_number", i + 1),
                    "description": step.get("description", ""),
                    "anxiety_rating": min(max(step.get("anxiety_rating", 50), 0), 100),
                    "duration_minutes": step.get("duration_minutes"),
                    "safety_behaviors_to_drop": step.get("safety_behaviors_to_drop", []),
                    "coping_strategies": step.get("coping_strategies", []),
                }
                validated_steps.append(validated_step)
            exercise["steps"] = validated_steps

        return exercise

    def _construct_exercise_from_state(self, state: GraphState) -> dict:
        """Construct a basic exercise structure from state when JSON parsing fails."""
        user_request = state.get("user_request", {})
        current_draft = state.get("current_draft", "")

        return {
            "exercise_type": user_request.get("exercise_type", "other"),
            "title": f"CBT Exercise for {user_request.get('target_condition', 'Anxiety')}",
            "target_condition": user_request.get("target_condition", "Anxiety"),
            "introduction": current_draft[:500] if current_draft else "",
            "steps": [],
            "safety_notes": [
                "If you experience significant distress, please stop and consult a mental health professional.",
                "This exercise is not a substitute for professional treatment.",
            ],
            "therapist_notes": "Exercise requires professional guidance for optimal implementation.",
            "contraindications": [
                "Active suicidal ideation",
                "Severe dissociation",
                "Untreated trauma",
            ],
            "evidence_base": "Based on standard CBT protocols",
        }
