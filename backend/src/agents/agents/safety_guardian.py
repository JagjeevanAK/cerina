"""Safety Guardian agent for reviewing CBT exercises for safety concerns."""

import json
import re
from typing import Any

from src.agents.config.prompts import SAFETY_GUARDIAN_PROMPT
from src.agents.state.graph_state import GraphState
from src.agents.agents.base import BaseAgent


class SafetyGuardianAgent(BaseAgent):
    """Agent responsible for safety review of CBT exercises."""

    agent_id: str = "safety_guardian"
    description: str = "Reviews CBT exercises for self-harm risks, medical advice boundaries, and crisis situations"

    def get_system_prompt(self, state: GraphState) -> str:
        """Get the system prompt for the safety guardian."""
        current_draft = state.get("current_draft", "")
        return SAFETY_GUARDIAN_PROMPT.format(current_draft=current_draft)

    async def process(self, state: GraphState) -> dict[str, Any]:
        """Review the current draft for safety concerns."""
        system_prompt = self.get_system_prompt(state)

        user_message = """Please review the draft for safety concerns and provide:
1. Specific safety flags with line references if applicable
2. Safety scores (self_harm_risk, medical_advice_risk, overall_safety_score)
3. Whether the draft passes safety review (overall_safety_score >= 0.8)
4. Actionable feedback if revision is needed

Format your response as:
## Safety Assessment

### Flagged Concerns:
[List specific concerns]

### Scores:
- self_harm_risk: [0-1]
- medical_advice_risk: [0-1]
- overall_safety_score: [0-1]
- crisis_escalation_needed: [true/false]

### Verdict:
[PASS/FAIL]

### Feedback for Revision:
[Specific actionable feedback if FAIL]"""

        response = await self.chat(system_prompt, user_message)

        # Parse the response
        safety_metrics = self._parse_safety_response(response)

        # Update scratchpad with findings
        scratchpad = self._get_scratchpad(state)
        scratchpad["last_action"] = "safety_review_complete"

        # Add notes for flagged concerns
        if not safety_metrics["passed"]:
            for phrase in safety_metrics.get("flagged_phrases", []):
                self._add_note(
                    scratchpad,
                    note_type="flag",
                    content=phrase,
                    severity="major" if safety_metrics["self_harm_risk"] > 0.5 else "minor",
                )

        self._add_note(
            scratchpad,
            note_type="info",
            content=f"Safety review: {'PASSED' if safety_metrics['passed'] else 'FAILED'} (score: {safety_metrics['overall_safety_score']:.2f})",
            severity="info" if safety_metrics["passed"] else "major",
        )

        # Update quality metrics
        quality_metrics = state.get("quality_metrics", {}).copy()
        quality_metrics["safety"] = {
            "self_harm_risk": safety_metrics["self_harm_risk"],
            "medical_advice_risk": safety_metrics["medical_advice_risk"],
            "crisis_escalation_needed": safety_metrics["crisis_escalation_needed"],
            "overall_safety_score": safety_metrics["overall_safety_score"],
            "flagged_phrases": safety_metrics.get("flagged_phrases", []),
            "passed": safety_metrics["passed"],
            "reviewed": True,
        }

        # Determine next stage
        if safety_metrics["passed"]:
            next_stage = "clinical_review"
        else:
            next_stage = "revising"

        return {
            "quality_metrics": quality_metrics,
            "scratchpads": {self.agent_id: scratchpad},
            "workflow_stage": next_stage,
        }

    def _parse_safety_response(self, response: str) -> dict:
        """Parse the safety review response to extract metrics."""
        # Default values
        metrics = {
            "self_harm_risk": 0.0,
            "medical_advice_risk": 0.0,
            "crisis_escalation_needed": False,
            "overall_safety_score": 1.0,
            "flagged_phrases": [],
            "passed": True,
        }

        response_lower = response.lower()

        # Parse scores using regex
        patterns = {
            "self_harm_risk": r"self_harm_risk:\s*([0-9.]+)",
            "medical_advice_risk": r"medical_advice_risk:\s*([0-9.]+)",
            "overall_safety_score": r"overall_safety_score:\s*([0-9.]+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, response_lower)
            if match:
                try:
                    value = float(match.group(1))
                    metrics[key] = min(max(value, 0.0), 1.0)  # Clamp to [0, 1]
                except ValueError:
                    pass

        # Parse crisis escalation
        if "crisis_escalation_needed: true" in response_lower:
            metrics["crisis_escalation_needed"] = True

        # Parse verdict
        if "verdict" in response_lower:
            if "fail" in response_lower.split("verdict")[1][:50].lower():
                metrics["passed"] = False
        elif metrics["overall_safety_score"] < 0.8:
            metrics["passed"] = False

        # Extract flagged concerns
        if "flagged concerns:" in response_lower:
            concerns_section = response.split("Flagged Concerns:")[-1]
            if "###" in concerns_section:
                concerns_section = concerns_section.split("###")[0]
            # Extract bullet points
            concerns = re.findall(r"[-•]\s*(.+)", concerns_section)
            metrics["flagged_phrases"] = [c.strip() for c in concerns if c.strip()]

        return metrics
