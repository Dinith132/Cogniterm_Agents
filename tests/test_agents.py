#!/usr/bin/env python3
"""
Basic tests for the multi-agent orchestration system
"""

import sys
import os
import unittest

# Add the parent directory to the path so we can import the agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.planner_agent import PlannerAgent
from agents.coder_agent import CoderAgent
from agents.debugger_agent import DebuggerAgent
from agents.summarizer_agent import SummarizerAgent
from utils.validation import validate_ip_address, validate_cidr_range


class TestPlannerAgent(unittest.TestCase):
    """Test cases for the Planner Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.planner = PlannerAgent()
    
    def test_plan_network_request(self):
        """Test planning a network scanning request"""
        request = "scan my local network for Android devices"
        plan = self.planner.plan_request(request)
        
        self.assertEqual(plan["request"], request)
        self.assertIsInstance(plan["steps"], list)
        self.assertGreater(len(plan["steps"]), 0)
        
        # Check that each step has required fields
        for step in plan["steps"]:
            self.assertIn("id", step)
            self.assertIn("description", step)
            self.assertIn("expected_input", step)
            self.assertIn("expected_output", step)
            self.assertIn("validation_rule", step)


class TestCoderAgent(unittest.TestCase):
    """Test cases for the Coder Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.coder = CoderAgent()
    
    def test_generate_code_network_range(self):
        """Test generating code for network range identification"""
        step = {
            "id": "step_1",
            "description": "Identify network range to scan",
            "expected_input": "None",
            "expected_output": "Network range in CIDR notation",
            "validation_rule": "Output should be a valid CIDR range like 192.168.1.0/24"
        }
        
        result = self.coder.generate_code(step, {})
        
        self.assertEqual(result["step_id"], "step_1")
        self.assertIn("code", result)
        self.assertIn("language", result)
        self.assertIn("reasoning", result)
        self.assertIn("expected_output", result)


class TestDebuggerAgent(unittest.TestCase):
    """Test cases for the Debugger Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.debugger = DebuggerAgent()
    
    def test_debug_code_syntax_error(self):
        """Test debugging code with syntax error"""
        step = {
            "id": "step_1",
            "description": "Identify network range to scan",
            "expected_input": "None",
            "expected_output": "Network range in CIDR notation",
            "validation_rule": "Output should be a valid CIDR range like 192.168.1.0/24"
        }
        
        code_result = {
            "step_id": "step_1",
            "code": "print('Hello World'",
            "language": "python",
            "reasoning": "Print a greeting",
            "expected_output": "Hello World"
        }
        
        error_info = {
            "error_message": "SyntaxError: unexpected EOF while parsing",
            "error_type": "syntax"
        }
        
        result = self.debugger.debug_code(step, code_result, error_info)
        
        self.assertEqual(result["step_id"], "step_1")
        self.assertIn("fixed_code", result)
        self.assertIn("error_type", result)
        self.assertIn("reasoning", result)


class TestSummarizerAgent(unittest.TestCase):
    """Test cases for the Summarizer Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.summarizer = SummarizerAgent()
    
    def test_generate_summary(self):
        """Test generating a summary report"""
        original_request = "scan my local network for Android devices"
        step_results = {
            "step_1": "192.168.1.0/24",
            "step_2": ["192.168.1.1", "192.168.1.10", "192.168.1.15"],
            "step_3": ["192.168.1.10"]
        }
        planned_steps = [
            {
                "id": "step_1",
                "description": "Identify network range to scan",
                "expected_input": "None",
                "expected_output": "Network range in CIDR notation",
                "validation_rule": "Output should be a valid CIDR range like 192.168.1.0/24"
            },
            {
                "id": "step_2",
                "description": "Scan network for active devices",
                "expected_input": "Network range from step_1",
                "expected_output": "List of active IP addresses",
                "validation_rule": "Output should be a list of valid IP addresses"
            },
            {
                "id": "step_3",
                "description": "Identify Android devices from active IPs",
                "expected_input": "List of active IP addresses from step_2",
                "expected_output": "List of IP addresses that are Android devices",
                "validation_rule": "Output should be a subset of the input IP list"
            }
        ]
        
        summary = self.summarizer.generate_summary(original_request, step_results, planned_steps)
        
        self.assertEqual(summary["original_request"], original_request)
        self.assertIn("steps_completed", summary)
        self.assertIn("key_results", summary)
        self.assertIn("final_outcome", summary)
        self.assertIn("warnings", summary)


class TestValidationUtils(unittest.TestCase):
    """Test cases for validation utilities"""
    
    def test_validate_ip_address(self):
        """Test IP address validation"""
        self.assertTrue(validate_ip_address("192.168.1.1"))
        self.assertTrue(validate_ip_address("10.0.0.1"))
        self.assertFalse(validate_ip_address("256.1.1.1"))
        self.assertFalse(validate_ip_address("192.168.1"))
        self.assertFalse(validate_ip_address("not.an.ip.address"))
    
    def test_validate_cidr_range(self):
        """Test CIDR range validation"""
        self.assertTrue(validate_cidr_range("192.168.1.0/24"))
        self.assertTrue(validate_cidr_range("10.0.0.0/8"))
        self.assertFalse(validate_cidr_range("192.168.1.0/33"))
        self.assertFalse(validate_cidr_range("256.1.1.0/24"))
        self.assertFalse(validate_cidr_range("192.168.1.0"))


if __name__ == "__main__":
    unittest.main()