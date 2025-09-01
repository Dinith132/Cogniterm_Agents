#!/usr/bin/env python3
"""
Base agent class for the multi-agent orchestration system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system
    """
    
    def __init__(self, name: str = "BaseAgent"):
        """
        Initialize the base agent
        
        Args:
            name (str): Name of the agent
        """
        self.name = name
    
    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and return updated state
        
        Args:
            state (dict): Current state of the workflow
            
        Returns:
            dict: Updated state
        """
        pass
    
    def _validate_state(self, state: Dict[str, Any], required_keys: list) -> bool:
        """
        Validate that required keys are present in state
        
        Args:
            state (dict): State to validate
            required_keys (list): List of required keys
            
        Returns:
            bool: Whether all required keys are present
        """
        return all(key in state for key in required_keys)
    
    def _log_info(self, message: str):
        """
        Log informational message
        
        Args:
            message (str): Message to log
        """
        print(f"[{self.name}] {message}")
    
    def _log_error(self, message: str):
        """
        Log error message
        
        Args:
            message (str): Error message to log
        """
        print(f"[{self.name}] ERROR: {message}")