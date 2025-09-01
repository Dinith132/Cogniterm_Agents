#!/usr/bin/env python3
"""
Step Manager/Controller for the multi-agent orchestration system
"""

from agents.base_agent import BaseAgent
from typing import Dict, Any, Tuple
import json
from .llm_manager import LLMManager


class StepManager(BaseAgent):
    """
    Agent responsible for orchestrating the workflow execution
    """

    def __init__(self, llm_manager: LLMManager):
        super().__init__("StepManager")
        self.step_results = {}
        self.llm_manager = llm_manager

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate the workflow execution (stub for now).
        
        Args:
            state (dict): Current workflow state
        
        Returns:
            dict: Updated workflow state
        """
        self._log_info("Processing state in StepManager (not fully implemented yet).")
        return state

    def validate_result(
        self, current_step: Dict[str, Any], user_result: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate user's execution result for a given step using the LLM.

        Args:
            current_step (dict): The current step definition
            user_result (dict): Result from user execution

        Returns:
            tuple: (is_valid (bool), reason (str))
        """
        validation_rule = current_step.get("validation_rule", "")
        output = user_result.get("output", "")

        system_prompt = f"""
        You are a validation engine. 
        Rule: {validation_rule}
        Output to validate: {output}

        Return only a JSON object in the following format:
        {{
            "is_valid": true/false,
            "reason": "short explanation"
        }}
        """

        raw_response = self.llm_manager.generate_text(system_prompt)

        try:
            # Convert LLM response into dict
            response_json = json.loads(raw_response)
            is_valid = response_json.get("is_valid", False)
            reason = response_json.get("reason", "No reason provided.")
            print("------------------validation types------------------------")
            print(is_valid)
            print(reason)
            print("-----------------------------------------------------------")
            return is_valid, reason

        except Exception as e:
            self._log_error(
                f"LLM validation parsing failed: {e} | Response: {raw_response}"
            )
            return False, f"Parsing error: {str(e)}"
