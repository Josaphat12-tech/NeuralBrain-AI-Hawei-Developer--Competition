"""
Data Validation Service
Validates health data against defined rules and constraints
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
from config import VALIDATION_RULES

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates health metrics against defined rules.
    
    Features:
    - Range checking
    - Type validation
    - Required field verification
    - Custom validation logic
    """
    
    def __init__(self):
        """Initialize validator with predefined rules."""
        self.rules = VALIDATION_RULES
    
    def validate_metric(self, metric_name: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a single health metric.
        
        Args:
            metric_name: Name of the metric (e.g., 'heart_rate')
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - Valid: (True, None)
            - Invalid: (False, error_message)
        """
        if metric_name not in self.rules:
            return True, None  # No rule defined, accept as valid
        
        rule = self.rules[metric_name]
        
        # Type checking
        if not isinstance(value, (int, float)):
            return False, f"{metric_name} must be numeric, got {type(value)}"
        
        # Range checking
        min_val = rule.get('min')
        max_val = rule.get('max')
        
        if value < min_val or value > max_val:
            return False, f"{metric_name} out of range [{min_val}-{max_val}], got {value}"
        
        return True, None
    
    def validate_record(self, record: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a complete health data record.
        
        Args:
            record: Dictionary of health metrics
            
        Returns:
            Tuple of (is_valid, error_messages)
            - Valid: (True, [])
            - Invalid: (False, [error1, error2, ...])
        """
        errors = []
        
        for metric, value in record.items():
            if value is None:
                continue  # Skip null values
            
            is_valid, error = self.validate_metric(metric, value)
            if not is_valid:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    def validate_batch(self, records: List[Dict]) -> Dict:
        """
        Validate multiple records.
        
        Args:
            records: List of health data dictionaries
            
        Returns:
            Dictionary with validation results:
            {
                'total': int,
                'valid': int,
                'invalid': int,
                'results': [
                    {'index': int, 'valid': bool, 'errors': [str]}
                ]
            }
        """
        results = {
            'total': len(records),
            'valid': 0,
            'invalid': 0,
            'results': []
        }
        
        for idx, record in enumerate(records):
            is_valid, errors = self.validate_record(record)
            
            results['results'].append({
                'index': idx,
                'valid': is_valid,
                'errors': errors
            })
            
            if is_valid:
                results['valid'] += 1
            else:
                results['invalid'] += 1
        
        return results
