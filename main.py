#!/usr/bin/env python3
"""
Main entry point for the Multi-Agent Orchestration System with WebSocket streaming
"""

from typing import Any, Dict
from agents.planner_agent import PlannerAgent
from agents.step_manager import StepManager
from agents.coder_agent import CoderAgent
from agents.debugger_agent import DebuggerAgent
from agents.summarizer_agent import SummarizerAgent
from agents.llm_manager import LLMManager
import json
import asyncio
import datetime
import uuid


class MultiAgentOrchestrator:
    """
    Main orchestrator class that coordinates all agents in the system
    """

    def __init__(self, llm_manager: LLMManager, websocket=None):
        self.planner = PlannerAgent()
        self.step_manager = StepManager(llm_manager)
        self.coder = CoderAgent(llm_manager)
        self.debugger = DebuggerAgent(llm_manager)
        self.summarizer = SummarizerAgent(llm_manager)

        self.websocket = websocket  # async callback for streaming output

    async def _send_message(self, type_: str, request_id: str, data: Dict[str, Any], step_id: str = None):
        """Send a well-structured JSON message via WebSocket (and log to console)."""
        message = {
            "type": type_,
            "request_id": request_id,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "data": data
        }
        if step_id:
            message["step_id"] = step_id

        # Log to console
        print(f"[{type_}] {json.dumps(data, indent=2)}")

        # Send to WebSocket if available
        if self.websocket:
            try:
                await self.websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"⚠️ Failed to send to client: {e}")

    async def execute_request(self, user_request: str):
        # request_id = "req-001"  # TODO: generate dynamically if needed


# inside execute_request
        request_id = f"req-{uuid.uuid4().hex[:8]}"   # e.g. req-a1b2c3d4

        # Request start
        await self._send_message(
            "REQUEST_START",
            request_id,
            {"user_request": user_request}
        )

        # Planning
        await self._send_message("PLAN_START", request_id, {"message": "Loading Planning agent request..."})
        plan = await asyncio.to_thread(self.planner.plan_request, user_request)
        steps_list = [
            {"step_id": p["id"], "description": p["description"]}
            for p in plan["steps"]
        ]

        await self._send_message(
            "PLAN_STEPS",
            request_id,
            {"steps": steps_list}
        )
        await self._send_message("PLAN_COMPLETE", request_id, {"total_steps": len(plan["steps"])})

        # Step execution loop
        step_results = {}
        current_step_index = 0
        await self._send_message("EXEC_INIT", request_id, {"message": "==================Executing steps====================="})

        while current_step_index < len(plan["steps"]):
            current_step = plan["steps"][current_step_index]
            step_id = current_step['id']

            await self._send_message("STEP_START", request_id, {"description": current_step['description']}, step_id)

            code_result = await asyncio.to_thread(self.coder.generate_code, current_step, step_results)

            await self._send_message("STEP_REASONING", request_id, {"reasoning": code_result["reasoning"]}, step_id)
            await self._send_message("STEP_CODE", request_id, {"language": code_result.get("language", "python"), "code": code_result["code"]}, step_id)

            # First run (user executes)
            user_result = await self._prompt_user_execution(request_id, code_result, step_id)

            # Validation
            is_valid, reason = await asyncio.to_thread(self.step_manager.validate_result, current_step, user_result)
            if is_valid:
                await self._send_message("STEP_SUCCESS", request_id, {"message": reason, "output": user_result["output"]}, step_id)
                step_results[step_id] = user_result["output"]
                current_step_index += 1
                continue

            await self._send_message("STEP_FAIL", request_id, {"reason": reason}, step_id)

            # Debug loop (retry up to 2 times)
            retries = 0
            max_retries = 2
            last_code = code_result

            while retries < max_retries:
                await self._send_message(
                    "DEBUG_START",
                    request_id,
                    {"attempt": retries + 1, "max_attempts": max_retries},
                    step_id
                )

                error_info = {
                    "error_message": reason,
                    "user_output": user_result.get("output", ""),
                    "success": user_result.get("success", False)
                }
                fix = await asyncio.to_thread(self.debugger.debug_code, current_step, last_code, error_info)

                await self._send_message("DEBUG_REASONING", request_id, {"reasoning": fix["reasoning"]}, step_id)
                await self._send_message("DEBUG_CODE", request_id, {"language": fix["language"], "code": fix["fixed_code"]}, step_id)

                fixed_code_result = {
                    "step_id": step_id,
                    "code": fix["fixed_code"],
                    "language": fix["language"],
                    "reasoning": fix.get("reasoning", ""),
                    "expected_output": fix.get("expected_output", "")
                }

                user_result = await self._prompt_user_execution(request_id, fixed_code_result, step_id)
                is_valid, reason = await asyncio.to_thread(self.step_manager.validate_result, current_step, user_result)

                if is_valid:
                    await self._send_message("DEBUG_SUCCESS", request_id, {"message": reason, "output": user_result["output"]}, step_id)
                    step_results[step_id] = user_result["output"]
                    current_step_index += 1
                    break

                await self._send_message("DEBUG_FAIL", request_id, {"reason": reason}, step_id)

                last_code = fixed_code_result
                retries += 1

            if retries >= max_retries:
                await self._send_message("DEBUG_ABORT", request_id, {"message": f"Gave up after {max_retries} attempts."}, step_id)
                break  # stop workflow for partial summary

        # Summary generation
        await self._send_message("SUMMARY_START", request_id, {"message": "Loading summary report..."})
        summary = await asyncio.to_thread(self.summarizer.generate_summary, user_request, step_results, plan["steps"])
        await self._send_message("SUMMARY_REPORT", request_id, summary)
        await self._send_message("REQUEST_COMPLETE", request_id, {"status": "finished"})

        return summary

    async def _prompt_user_execution(self, request_id: str, code_result: Dict[str, Any], step_id: str) -> Dict[str, Any]:
        # Step 1: Ask client to execute the code
        await self._send_message(
            "STEP_EXECUTION_REQUEST",
            request_id,
            {"instructions": "Please execute the code and send back the output and success status.", "code": code_result["code"]},
            step_id
        )

        # Step 2: Wait for response
        while True:
            response = await self.websocket.receive_text()
            print("User response", response)
            return {
                "output": response,
                "success": True
            }
