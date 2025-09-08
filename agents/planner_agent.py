#!/usr/bin/env python3
"""
Planner Agent for the multi-agent orchestration system using Gemini AI
"""

from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import json
from .llm_manager import LLMManager


class PlannerAgent(BaseAgent):
    """
    Agent responsible for breaking down user requests into atomic steps
    using Gemini AI for dynamic plan generation
    """

    def __init__(self):
        """
        Initialize the Planner Agent
        """
        super().__init__("PlannerAgent")

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the user request and generate a plan dynamically via Gemini AI

        Args:
            state (dict): Current state containing user_request

        Returns:
            dict: Updated state with planned_steps
        """
        user_request = state.get("user_request", "")
        if not user_request:
            self._log_error("No user request provided")
            return state

        try:
            plan = self.plan_request(user_request)
        except Exception as e:
            self._log_error(f"Failed to generate plan: {e}")
            return state
        
        # Validate Gemini response structure
        steps = plan.get("steps", [])
        if not isinstance(steps, list) or not steps:
            self._log_error("Gemini returned invalid steps structure")
            return state

        return {
            "planned_steps": steps,
            "original_request": plan.get("request", user_request),
            "current_step_index": 0,
            "step_results": {}
        }

    def plan_request(self, user_request: str) -> Dict[str, Any]:
        """
        Send the user request to Gemini AI and parse the structured plan.

        Args:
            user_request (str): The user's high-level request

        Returns:
            dict: JSON structure containing the original request and ordered steps
        """
        # Construct system prompt for Gemini AI

        system_prompt = f"""
You are a Planner Agent with full knowledge of Linux systems. Assume you have access to a gnome terminal. 
Your task is to break down the following user request into a sequence of short, ordered atomic steps.
All steps are executed in the same terminal session; do NOT open a new terminal.

⚠️ Rules:
- Each step must be under 50 words.
- Do NOT explain or add extra text outside JSON.
- Return ONLY valid JSON, no markdown, no prose.
- Each step must include exactly these keys: 
  id, description, expected_input, expected_output, validation_rule
- validation_rule should describe **how to verify correctness in plain language**, not keyword matches.
- expected_output should describe the expected terminal output realistically.
- expected_input should be the exact command to run.
- Make steps sequential and atomic; each step must be independently executable.
- Assume the person or LLM will validate the output; write validation rules clearly and objectively. 
- When planing assume that this linux system have mmost of the lib preinstalled, so dont want to install in the tool in here 

User Request: "{user_request}"

Return your output as a JSON object with this format:
{{ 
"request": "<original user request>",
"steps": [
    {{
    "id": "<step id>",
    "description": "<short description>",
    "expected_input": "<command to run>",
    "expected_output": "<what the terminal shows>",
    "validation_rule": "<how to check that this step was done correctly>"
    }}
]
}}
"""


        # print("---------------------before call gem-------------------------")
        # Call Gemini API (replace with actual Gemini API call)
        gemini_response = gemini_api_call(system_prompt)
        # print("---------------------after call gem-------------------------")

        # print("====================================================")
        # print(gemini_response)
        # print("====================================================")
        
        # return gemini_response

        # Parse the response to JSON
        try:
            plan_json = json.loads(gemini_response.get("content", "{}"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response: {e}")


        return plan_json


# ----------------------------
# Helper: Replace this with actual Gemini API function
# ----------------------------
def gemini_api_call(prompt: str) -> Dict[str, Any]:
    """
    Mock function for Gemini AI API call. Replace with actual API call.
    Expected return format: {"content": "<JSON string>"}
    """
    # Example placeholder response

    llm_manager = LLMManager(api_key="AIzaSyCO590GfHqyGtSEKaCYtHSA4HhR0G-S12M")
    plan_text=llm_manager.generate_text(prompt)

    # print(plan_text)
    return {
        "content": plan_text
    }
