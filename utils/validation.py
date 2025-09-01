#!/usr/bin/env python3
"""
Validation utilities for the multi-agent orchestration system
"""

import re
from typing import Any, Dict, List


def validate_ip_address(ip: str) -> bool:
    """
    Validate if a string is a valid IP address
    
    Args:
        ip (str): IP address to validate
        
    Returns:
        bool: Whether the IP address is valid
    """
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    # Check that each octet is between 0 and 255
    octets = ip.split('.')
    for octet in octets:
        if int(octet) < 0 or int(octet) > 255:
            return False
            
    return True


def validate_cidr_range(cidr: str) -> bool:
    """
    Validate if a string is a valid CIDR range
    
    Args:
        cidr (str): CIDR range to validate
        
    Returns:
        bool: Whether the CIDR range is valid
    """
    pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
    if not re.match(pattern, cidr):
        return False
    
    # Validate IP part
    ip_part = cidr.split('/')[0]
    if not validate_ip_address(ip_part):
        return False
    
    # Validate subnet part
    subnet_part = int(cidr.split('/')[1])
    if subnet_part < 0 or subnet_part > 32:
        return False
        
    return True


def validate_output(output: Any, validation_rule: str) -> bool:
    """
    Validate output against a validation rule
    
    Args:
        output (Any): Output to validate
        validation_rule (str): Rule for validation
        
    Returns:
        bool: Whether validation passed
    """
    if "valid IP" in validation_rule:
        if isinstance(output, str):
            return validate_ip_address(output)
        elif isinstance(output, list):
            return all(validate_ip_address(ip) for ip in output)
    elif "CIDR" in validation_rule:
        if isinstance(output, str):
            return validate_cidr_range(output)
    elif "list of" in validation_rule:
        return isinstance(output, list)
    elif "structured list" in validation_rule:
        return isinstance(output, (list, str))
        
    # Default validation
    return bool(output)


def validate_step_result(step: Dict[str, Any], result: Any) -> bool:
    """
    Validate a step result against its validation rule
    
    Args:
        step (dict): Step definition with validation rule
        result (Any): Result to validate
        
    Returns:
        bool: Whether validation passed
    """
    return validate_output(result, step.get("validation_rule", ""))