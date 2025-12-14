"""Clinical Critic agent for evaluating tone, empathy, and clinical accuracy."""

import re
from typing import Any

from src.agents.config.prompts import CLINICAL_CRITIC_PROMPT
from src.agents.state.graph_state import GraphState
from src.agents.agents.base import BaseAgent


class ClinicalCriticAgent(BaseAgent):
    """Agent responsible for evaluating clinical tone and empathy."""

    agent_id: str = "clinical_critic"
    description: str = "Evaluates CBT exercises for warmth, clinical accuracy, and language accessibility"

    def get_system_prompt(self, state: GraphState) -> str:
        """Get the system prompt for the clinical critic."""
        current_draft = state.get("current_draft", "")

        # Get safety notes
        scratchpads = state.get("scratchpads", {})
        safety_scratchpad = scratchpads.get("safety_guardian", {})
        safety_notes = safety_scratchpad.get("notes", [])
        safety_notes_str = "\n".join(
            f"- {n.get('content', '')}" for n in safety_notes if not n.get("resolved")
        ) or "No safety notes."

        return CLINICAL_CRITIC_PROMPT.format(
            current_draft=current_draft,
            safety_notes=safety_notes_str,
        )

    async def process(self, state: GraphState) -> dict[str, Any]:
        """Evaluate the current draft for clinical quality and empathy."""
        system_prompt = self.get_system_prompt(state)

        user_message = """Please evaluate the draft and provide:
1. Warmth & Tone assessment
2. Clinical accuracy assessment
3. Language accessibility assessment
4. Specific tone issues to address
5. Overall empathy metrics

Format your response as:
## Clinical Assessment

### Warmth & Tone:
[Assessment with examples]
Score: [0-1]

### Clinical Accuracy:
[Assessment with examples]
Score: [0-1]

### Language Accessibility:
[Assessment with examples]
Score: [0-1]

### Tone Issues:
[List specific issues]

### Overall Empathy Score: [0-1]

### Verdict:
[PASS/FAIL]

### Feedback for Revision:
[Specific actionable feedback if FAIL]"""

        response = await self.chat(system_prompt, user_message)

        # Parse the response
        empathy_metrics = self._parse_empathy_response(response)

        # Update scratchpad
        scratchpad = self._get_scratchpad(state)
        scratchpad["last_action"] = "clinical_review_complete"

        # Add notes for tone issues
        for issue in empathy_metrics.get("tone_issues", []):
            self._add_note(
                scratchpad,
                note_type="suggestion",
                content=issue,
                severity="minor",
            )

        self._add_note(
            scratchpad,
            note_type="info",
            content=f"Clinical review: {'PASSED' if empathy_metrics['passed'] else 'FAILED'} (score: {empathy_metrics['overall_empathy_score']:.2f})",
            severity="info" if empathy_metrics["passed"] else "major",
        )

        # Update quality metrics
        quality_metrics = state.get("quality_metrics", {}).copy()
        quality_metrics["empathy"] = {
            "warmth_score": empathy_metrics["warmth_score"],
            "clinical_accuracy": empathy_metrics["clinical_accuracy"],
            "language_accessibility": empathy_metrics["language_accessibility"],
            "overall_empathy_score": empathy_metrics["overall_empathy_score"],
            "tone_issues": empathy_metrics.get("tone_issues", []),
            "passed": empathy_metrics["passed"],
            "reviewed": True,
        }

        # Check convergence
        safety_passed = quality_metrics.get("safety", {}).get("passed", False)
        empathy_passed = empathy_metrics["passed"]
        converged = safety_passed and empathy_passed
        quality_metrics["converged"] = converged

        # Determine next stage
        if converged:
            next_stage = "finalizing"
        else:
            next_stage = "revising"

        return {
            "quality_metrics": quality_metrics,
            "scratchpads": {self.agent_id: scratchpad},
            "workflow_stage": next_stage,
        }

    def _parse_empathy_response(self, response: str) -> dict:
        """Parse the clinical review response to extract metrics."""
        metrics = {
            "warmth_score": 0.5,
            "clinical_accuracy": 0.5,
            "language_accessibility": 0.5,
            "overall_empathy_score": 0.5,
            "tone_issues": [],
            "passed": False,
        }

        response_lower = response.lower()

        # Parse individual scores
        score_patterns = {
            "warmth_score": [
                r"warmth.*?score:\s*([0-9.]+)",
                r"warmth.*?:\s*([0-9.]+)",
            ],
            "clinical_accuracy": [
                r"clinical accuracy.*?score:\s*([0-9.]+)",
                r"clinical accuracy.*?:\s*([0-9.]+)",
            ],
            "language_accessibility": [
                r"language accessibility.*?score:\s*([0-9.]+)",
                r"accessibility.*?score:\s*([0-9.]+)",
            ],
            "overall_empathy_score": [
                r"overall empathy score:\s*([0-9.]+)",
                r"empathy score:\s*([0-9.]+)",
            ],
        }

        for key, patterns in score_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, response_lower)
                if match:
                    try:
                        value = float(match.group(1))
                        metrics[key] = min(max(value, 0.0), 1.0)
                        break
                    except ValueError:
                        pass

        # Calculate overall if not found
        if metrics["overall_empathy_score"] == 0.5:
            avg = (
                metrics["warmth_score"]
                + metrics["clinical_accuracy"]
                + metrics["language_accessibility"]
            ) / 3
            metrics["overall_empathy_score"] = round(avg, 2)

        # Parse verdict
        if "verdict" in response_lower:
            verdict_section = response_lower.split("verdict")[1][:50]
            metrics["passed"] = "pass" in verdict_section and "fail" not in verdict_section
        else:
            metrics["passed"] = metrics["overall_empathy_score"] >= 0.7

        # Extract tone issues
        if "tone issues:" in response_lower:
            issues_section = response.split("Tone Issues:")[-1]
            if "###" in issues_section:
                issues_section = issues_section.split("###")[0]
            issues = re.findall(r"[-•]\s*(.+)", issues_section)
            metrics["tone_issues"] = [i.strip() for i in issues if i.strip()]

        return metrics
