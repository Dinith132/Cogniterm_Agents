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
import json
from agents.llm_manager import LLMManager
import asyncio


class MultiAgentOrchestrator:
    """
    Main orchestrator class that coordinates all agents in the system
    """
    
    def __init__(self, llm_manager: LLMManager, websocket=None):
        self.planner = PlannerAgent()                   # done
        self.step_manager = StepManager(llm_manager)    # done
        self.coder = CoderAgent(llm_manager)            # done
        self.debugger = DebuggerAgent(llm_manager)      # not completed
        self.summarizer = SummarizerAgent(llm_manager)  # done

        self.websocket = websocket  # async callback for streaming output

    async def _send_output(self, message: str, topic: str = "GENERAL"):
        print(f"[{topic}] {message}")
        if self.websocket:
            try:
                await self.websocket.send_text(json.dumps({
                    "type": "INFO",
                    "topic": topic,
                    "message": message
                }))
            except Exception as e:
                print(f"Failed to send to client: {e}")


    async def execute_request(self, user_request: str):
        # print("---------------------------------------")
        await self._send_output(f"Processing request: {user_request}", topic="REQUEST")
        await self._send_output("Loading Planning agent request...")
        # print("---------------------------------------")

        # plan = self.planner.plan_request(user_request)
        plan = await asyncio.to_thread(self.planner.plan_request, user_request)
        for p in plan['steps']:
            await self._send_output(f"{p['id']} : {p['description']}", topic="PLAN")

        await self._send_output("==================Executing steps=====================", topic="EXEC INIT")
        step_results = {}
        current_step_index = 0

        while current_step_index < len(plan["steps"]):
            current_step = plan["steps"][current_step_index]
            await self._send_output(f"\nLoading step {current_step['id']}: {current_step['description']}...", topic=f"STEP_{current_step['id']}")

            # code_result = self.coder.generate_code(current_step, step_results)
            code_result = await asyncio.to_thread(self.coder.generate_code, current_step, step_results)

            await self._send_output(code_result["reasoning"], topic=f"STEP_{current_step['id']}_REASONING")
            await self._send_output(code_result["code"], topic=f"STEP_{current_step['id']}_CODE")


            # First run (user executes)
            print("++++++++++++++check point++++++++++++++++++++++++++++++")
            user_result = await self._prompt_user_execution(code_result)
            print("....",user_request)
            print("++++++++++++++check point end++++++++++++++++++++++++++++++")

            # Validate
            print("+++++++++++++++validation start++++++++++++++++=")
            # is_valid, reason = self.step_manager.validate_result(current_step, user_result)
            is_valid, reason = await asyncio.to_thread(self.step_manager.validate_result, current_step, user_result)
            print("+++++++++++++++validation done++++++++++++++++=")
            if is_valid:
                await self._send_output(
                    f"✅ Step {current_step['id']} succeeded: {reason}",
                    topic=f"STEP_{current_step['id']}_SUCCESS"
                )
                step_results[current_step["id"]] = user_result["output"]
                current_step_index += 1
                continue

            await self._send_output(
                f"❌ Step {current_step['id']} failed: {reason}",
                topic=f"STEP_{current_step['id']}_FAIL"
            )
            # Debug loop (retry up to 2 times)
            retries = 0
            max_retries = 2
            last_code = code_result

            while retries < max_retries:
                await self._send_output(
                    f"\n--- Debug attempt {retries+1}/{max_retries} ---",
                    topic=f"DEBUG_STEP_{current_step['id']}_ATTEMPT_{retries+1}"
                )

                error_info = {
                    "error_message": reason,
                    "user_output": user_result.get("output", ""),
                    "success": user_result.get("success", False)
                }
                # fix = self.debugger.debug_code(current_step, last_code, error_info)
                fix = await asyncio.to_thread(self.debugger.debug_code, current_step, last_code, error_info)

                # Debug reasoning
                await self._send_output(
                    fix["reasoning"],
                    topic=f"DEBUG_STEP_{current_step['id']}_REASONING_ATTEMPT_{retries+1}"
                )

                # Debug fixed code
                await self._send_output(
                    fix["fixed_code"],
                    topic=f"DEBUG_STEP_{current_step['id']}_CODE_ATTEMPT_{retries+1}"
                )

                # Ask user to execute the fixed code
                fixed_code_result = {
                    "step_id": current_step["id"],
                    "code": fix["fixed_code"],
                    "language": fix["language"],
                    "reasoning": fix.get("reasoning", ""),
                    "expected_output": fix.get("expected_output", "")
                }
                print("++++++++++++++check point++++++++++++++++++++++++++++++")
                user_result = await self._prompt_user_execution(fixed_code_result)
                print("++++++++++++++check point end++++++++++++++++++++++++++++++")
                # is_valid, reason = self.step_manager.validate_result(current_step, user_result)
                is_valid, reason = await asyncio.to_thread(self.step_manager.validate_result, current_step, user_result)
                if is_valid:
                    await self._send_output(
                        f"✅ Step {current_step['id']} succeeded after debugging: {reason}",
                        topic=f"STEP_{current_step['id']}_SUCCESS_AFTER_DEBUG"
                    )
                    step_results[current_step["id"]] = user_result["output"]
                    current_step_index += 1
                    break

                await self._send_output(
                    f"❌ Still failing: {reason}",
                    topic=f"DEBUG_STEP_{current_step['id']}_FAIL_ATTEMPT_{retries+1}"
                )

                last_code = fixed_code_result
                retries += 1

            if retries >= max_retries:
                await self._send_output(f"⚠️ Giving up on Step {current_step['id']} after {max_retries} attempts.")
                break  # stop workflow for partial summary

        # Summary generation
        await self._send_output(
            "Loading summary report...",
            topic="SUMMARY_START"
        )
        # summary = self.summarizer.generate_summary(user_request, step_results, plan["steps"])
        summary = await asyncio.to_thread(self.summarizer.generate_summary, user_request, step_results, plan["steps"])
        # await self._send_output(json.dumps(summary, indent=2))

        return summary

    async def _prompt_user_execution(self, code_result: Dict[str, Any]) -> Dict[str, Any]:
        # Step 1: Ask client to execute the code
        await self.websocket.send_text(json.dumps({
            "type": "EXECUTE_CODE_REQUEST",
            "code": code_result["code"],   # Send the code snippet
            "instructions": "Please execute the code above and send back the output and success status."
        }))

        # Step 2: Wait for response
        while True:
            response = await self.websocket.receive_text()
            print("User response", response)
            return {
                "output": response,
                "success": True
            }
