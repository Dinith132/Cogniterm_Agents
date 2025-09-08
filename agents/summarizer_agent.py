#!/usr/bin/env python3
"""
Summarizer Agent for the multi-agent orchestration system using LLM
"""

from agents.base_agent import BaseAgent
from agents.llm_manager import LLMManager
from typing import Dict, Any, List
import json


class SummarizerAgent(BaseAgent):
    """
    Agent responsible for generating final summary reports using LLMManager
    """
    
    def __init__(self, llm_manager: LLMManager):
        """
        Initialize the Summarizer Agent
        """
        super().__init__("SummarizerAgent")
        self.llm_manager = llm_manager
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a final summary report
        
        Args:
            state (dict): Current state containing original request, step results, and planned steps
            
        Returns:
            dict: Updated state with final summary
        """
        original_request = state.get("original_request", "")
        step_results = state.get("step_results", {})
        planned_steps = state.get("planned_steps", [])
        
        if not original_request or not planned_steps:
            self._log_error("Missing required information for summarization")
            return state
        
        summary = self.generate_summary(original_request, step_results, planned_steps)
        return {
            "final_report": summary,
            "process_complete": True
        }
    
    def generate_summary(
        self, 
        original_request: str, 
        step_results: Dict[str, Any], 
        planned_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use LLMManager to generate a final summary report
        
        Args:
            original_request (str): The original user request
            step_results (dict): Results from all completed steps
            planned_steps (list): The original planned steps
            
        Returns:
            dict: JSON structure containing the final report
        """
        # Convert steps and results into strings for the prompt
        steps_str = "\n".join(
            f"{step['id']}: {step['description']} -> Result: {step_results.get(step['id'], 'No result')}"
            for step in planned_steps
        )
        
#         prompt = f"""
# You are an AI assistant. The user requested: "{original_request}".

# The workflow had the following steps and results:
# {steps_str}

# Instructions:
# - Summarize each step and its outcome concisely.
# - Highlight key results.
# - Identify any warnings or errors.
# - Determine the final outcome (success, partial, or failure).
# - Return output strictly as a JSON object with the keys: original_request, steps_completed, key_results, final_outcome, warnings.
# """
        

        prompt = f"""
You are an AI assistant specialized in summarizing workflows. 

The user requested: "{original_request}".

The workflow had the following steps and results:
{steps_str}

Instructions:
- Summarize each step and its outcome concisely.
- Highlight key results.
- Identify any warnings or errors.
- Determine the final outcome: "success", "partial", or "failure".
- Return the output strictly as a JSON object with the following keys:

    {{
        "original_request": "<copy of the original request>",
        "steps_completed": [
            {{
                "step_description": "<description of step>",
                "outcome": "<result of step>"
            }},
            ...
        ],
        "key_results": ["<list of key results>"],
        "total_summary": "<concise summary including all key_results, the final_outcome, and any warnings/errors>",
        "final_outcome": "<success | partial | failure>",
        "warnings": ["<list of warnings or errors, empty if none>"]
    }}"""

        # Call LLMManager
        llm_response_text = self.llm_manager.generate_text(prompt)
        
        # Attempt to parse JSON returned by LLM
        try:
            llm_response = json.loads(llm_response_text)
        except json.JSONDecodeError:
            self._log_error("LLM returned invalid JSON. Returning fallback summary.")
            llm_response = {
                "original_request": original_request,
                "steps_completed": planned_steps,
                "key_results": "LLM summary failed",
                "total_summary":"Failed",
                "final_outcome": "Unknown",
                "warnings": []
            }
        
        return llm_response
