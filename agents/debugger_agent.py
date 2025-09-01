#!/usr/bin/env python3
"""
Debugger Agent for the multi-agent orchestration system (LLM-driven)
"""

from agents.base_agent import BaseAgent
from typing import Dict, Any, Tuple
import json
import re
from .llm_manager import LLMManager


class DebuggerAgent(BaseAgent):
    """
    Agent responsible for debugging failed code executions using an LLM
    """

    def __init__(self, llm_manager: LLMManager):
        super().__init__("DebuggerAgent")
        self.llm_manager = llm_manager

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optional: Not used directly in this flow. You can leave this as a stub
        or wire a stateful debugging flow if needed.
        """
        self._log_info("DebuggerAgent.process called (stub).")
        return state

    def debug_code(
        self,
        step: Dict[str, Any],
        code_result: Dict[str, Any],
        error_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ask the LLM to analyze the failure and return a JSON-only fix:
        {
          "step_id": "...",
          "error_type": "syntax|runtime|environment|logic",
          "reasoning": "...",
          "fixed_code": "<runnable code>",
          "language": "<lang>",
          "expected_output": "<what to expect>"
        }
        """
        prompt = f"""
You are a Debugger Agent. Analyze a failed code execution and provide a minimal, correct fix.

Return ONLY a valid JSON object. No markdown, no commentary.

Constraints:
- Keep the fix minimal but correct.
- Keep the language the same unless the bug requires a language change.
- Include a short reasoning and an error_type (syntax|runtime|environment|logic).

Inputs:
- Step (goal & validation): {json.dumps(step, ensure_ascii=False)}
- Original code result: {json.dumps(code_result, ensure_ascii=False)}
- Error info from user execution: {json.dumps(error_info, ensure_ascii=False)}

JSON schema:
{{
  "step_id": "string",
  "error_type": "syntax|runtime|environment|logic",
  "reasoning": "string",
  "fixed_code": "string",
  "language": "string",
  "expected_output": "string"
}}
"""

        raw = self.llm_manager.generate_text(prompt)
        cleaned = self._extract_json(raw)
        try:
            data = json.loads(cleaned)
        except Exception as e:
            self._log_error(f"DebuggerAgent: JSON parse failed: {e} | raw={raw}")
            # Fallback: return a safe, pass-through structure
            return {
                "step_id": step.get("id", "unknown"),
                "error_type": "logic",
                "reasoning": "LLM returned malformed JSON; falling back to original code.",
                "fixed_code": code_result.get("code", ""),
                "language": code_result.get("language", "python"),
                "expected_output": code_result.get("expected_output", "")
            }
        # sanity fill
        data.setdefault("step_id", step.get("id", "unknown"))
        data.setdefault("language", code_result.get("language", "python"))
        data.setdefault("expected_output", code_result.get("expected_output", ""))
        return data

    # --- helpers ---

    def _extract_json(self, text: str) -> str:
        """
        Robustly extract a JSON object from LLM output:
        - strips ```json fences
        - if multiple braces/no fences, tries to grab the first {...} block
        """
        t = re.sub(r"^```json\s*|\s*```$", "", str(text).strip(), flags=re.MULTILINE).strip()
        # If it's already valid JSON, great.
        if self._looks_like_json(t):
            return t
        # Try to find the first {...} block
        match = re.search(r"\{.*\}", t, flags=re.DOTALL)
        if match:
            return match.group(0).strip()
        return t

    def _looks_like_json(self, s: str) -> bool:
        try:
            json.loads(s)
            return True
        except Exception:
            return False
