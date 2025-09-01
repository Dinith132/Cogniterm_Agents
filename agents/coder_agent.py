#!/usr/bin/env python3
"""
Coder Agent for the multi-agent orchestration system
"""

import json
from typing import Dict, Any
from agents.base_agent import BaseAgent
from agents.llm_manager import LLMManager
from pprint import pprint
import re

class CoderAgent(BaseAgent):
    """
    Agent responsible for generating executable code for steps
    """

    def __init__(self, llm_manager: LLMManager):
        """
        Initialize the Coder Agent with an LLM manager
        """
        super().__init__("CoderAgent")
        self.llm_manager = llm_manager

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate code for the current step

        Args:
            state (dict): Current state containing current_step and step_results

        Returns:
            dict: Updated state with generated code
        """
        current_step = state.get("current_step", {})
        step_results = state.get("step_results", {})

        if not current_step:
            self._log_error("No current step provided")
            return state

        code_result = self.generate_code(current_step, step_results)
        return {"code_to_execute": code_result}

    def generate_code(self, step: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executable code for a specific step via LLM

        Args:
            step (dict): The step to generate code for
            previous_results (dict): Results from previous steps

        Returns:
            dict: JSON structure containing code, language, reasoning, and expected output
        """
        # Construct the system prompt for code generation
        system_prompt = f"""
        You are a Coder Agent. Your job is to write executable code for a given step.

        ⚠️ Rules:
        - Respond ONLY with a valid JSON object. No markdown, no explanations outside JSON.
        - Must return these keys: step_id, code, language, reasoning, expected_output.
        - Code must be directly runnable in the specified language.
        - Be concise but correct.
        - try to give code in zsh or bash
        Step to implement:
        {json.dumps(step, indent=2)}

        Previous step results (if any):
        {json.dumps(previous_results, indent=2)}

        Example JSON format:

        {{
          "step_id": "step_1",
          "code": "<runnable code>",
          "language": "bash",
          "reasoning": "<short reasoning why this code solves the step>",
          "expected_output": "<what the code will output>"
        }}
        """

        # Call the LLM through LLMManager
        raw_response = self.llm_manager.generate_text(system_prompt)

        # print("****************************************************************8")
        # pprint(raw_response)
        # print("****************************************************************8")

        cleaned_response = re.sub(r"^```json\s*|\s*```$", "", raw_response, flags=re.MULTILINE).strip()


        # Parse JSON safely
        try:
            response_json = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"CoderAgent: Failed to parse LLM response: {e}\nResponse was: {raw_response}")

        return response_json
