#!/usr/bin/env python3
"""
Example usage of the multi-agent orchestration system for network scanning
"""

import sys
import os

# Add the parent directory to the path so we can import the agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.planner_agent import PlannerAgent
from agents.coder_agent import CoderAgent
from agents.summarizer_agent import SummarizerAgent


def main():
    """
    Example demonstrating the network scanning workflow
    """
    print("Multi-Agent Orchestration System - Network Scanner Example")
    print("=" * 60)
    
    # Initialize agents
    planner = PlannerAgent()
    coder = CoderAgent()
    summarizer = SummarizerAgent()
    
    # Example request
    user_request = "scan my local network for Android devices"
    print(f"User Request: {user_request}\n")
    
    # Step 1: Plan the request
    print("Step 1: Planning request...")
    plan = planner.plan_request(user_request)
    print(f"Generated {len(plan['steps'])} steps:\n")
    
    for i, step in enumerate(plan['steps'], 1):
        print(f"  Step {i}: {step['description']}")
        print(f"    Expected Input: {step['expected_input']}")
        print(f"    Expected Output: {step['expected_output']}")
        print(f"    Validation Rule: {step['validation_rule']}\n")
    
    # Step 2: Generate code for each step
    print("Step 2: Generating code for each step...\n")
    step_results = {}
    
    for step in plan['steps']:
        print(f"Generating code for: {step['description']}")
        code_result = coder.generate_code(step, step_results)
        print(f"Language: {code_result['language']}")
        print(f"Reasoning: {code_result['reasoning']}")
        print("Generated Code:")
        print("-" * 40)
        print(code_result['code'])
        print("-" * 40)
        
        # Simulate execution result
        step_results[step['id']] = f"Simulated result for {step['id']}"
        print(f"Simulated Result: {step_results[step['id']]}\n")
    
    # Step 3: Generate summary
    print("Step 3: Generating summary report...")
    summary = summarizer.generate_summary(user_request, step_results, plan['steps'])
    
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(f"Original Request: {summary['original_request']}")
    print(f"Final Outcome: {summary['final_outcome']}")
    print(f"Key Results: {summary['key_results']}")
    
    if summary['warnings']:
        print("\nWarnings:")
        for warning in summary['warnings']:
            print(f"  - {warning}")
    
    print("\nSteps Completed:")
    for step in summary['steps_completed']:
        print(f"  - {step['description']}: {step['result']}")


if __name__ == "__main__":
    main()