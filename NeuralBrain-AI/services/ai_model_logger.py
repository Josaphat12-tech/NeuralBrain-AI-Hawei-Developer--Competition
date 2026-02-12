"""
AI Model Logging and Usage Tracking Service
Logs which AI model (OpenAI, Groq, Gemini) completed each task

Author: Bitingo Josaphat JB
"""

import logging
import time
from datetime import datetime
from functools import wraps
from models import db, IngestionLog

logger = logging.getLogger(__name__)


class AIModelLogger:
    """
    Comprehensive AI Model usage tracking and logging
    """
    
    # Model provider mapping
    PROVIDERS = {
        'gpt-3.5-turbo': 'openai',
        'gpt-4': 'openai',
        'gpt-4-turbo': 'openai',
        'groq-mixtral': 'groq',
        'groq-llama2': 'groq',
        'gemini-pro': 'google',
        'gemini-1.5': 'google',
        'claude-3': 'anthropic',
        'huawei-pangu': 'huawei'
    }
    
    # Task categories
    TASKS = {
        'risk_scoring': 'Risk Assessment',
        'prediction': 'Outbreak Prediction',
        'analysis': 'Data Analysis',
        'alerts': 'Alert Generation',
        'classification': 'Disease Classification',
        'normalization': 'Data Normalization'
    }
    
    @staticmethod
    def get_provider(model_name):
        """Get provider from model name"""
        for model, provider in AIModelLogger.PROVIDERS.items():
            if model in model_name.lower():
                return provider
        return 'unknown'
    
    @staticmethod
    def log_task_completion(model_name, task, success, response_time_ms=None, error=None, data=None):
        """
        Log when an AI model completes a task
        
        Args:
            model_name (str): Model identifier ('gpt-4', 'groq-mixtral', etc.)
            task (str): Task type ('risk_scoring', 'prediction', etc.)
            success (bool): Whether task succeeded
            response_time_ms (float): Response time in milliseconds
            error (str): Error message if failed
            data (dict): Additional data to log
        """
        provider = AIModelLogger.get_provider(model_name)
        task_label = AIModelLogger.TASKS.get(task, task)
        
        status = 'SUCCESS' if success else 'FAILED'
        time_str = f', response_time={response_time_ms}ms' if response_time_ms else ''
        error_str = f', error={error}' if error else ''
        
        log_msg = f'AI_MODEL_TASK [{status}] model={model_name}, provider={provider}, task={task}{time_str}{error_str}'
        
        if success:
            logger.info(f'✅ {log_msg}')
        else:
            logger.warning(f'⚠️ {log_msg}')
        
        # Log to database for tracking and analytics
        try:
            log_entry = IngestionLog(
                api_source=provider,
                status='success' if success else 'failed',
                execution_time=response_time_ms / 1000.0 if response_time_ms else None,
                error_message=error,
                details={
                    'model': model_name,
                    'task': task,
                    'provider': provider,
                    'task_label': task_label,
                    'additional_data': data or {}
                }
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log to database: {str(e)}")
    
    @staticmethod
    def log_model_switch(from_model, to_model, reason):
        """Log when switching between AI models"""
        from_provider = AIModelLogger.get_provider(from_model)
        to_provider = AIModelLogger.get_provider(to_model)
        logger.info(f'🔄 MODEL_SWITCH [{from_provider}→{to_provider}] from {from_model} to {to_model}: {reason}')
    
    @staticmethod
    def log_model_error(model_name, task, error):
        """Log model errors for debugging"""
        provider = AIModelLogger.get_provider(model_name)
        logger.error(f'❌ MODEL_ERROR [{provider}] model={model_name}, task={task}, error={error}')
        
        # Log to database
        try:
            log_entry = IngestionLog(
                api_source=provider,
                status='error',
                error_message=error,
                details={
                    'model': model_name,
                    'task': task,
                    'provider': provider,
                    'error_type': 'model_error'
                }
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log error to database: {str(e)}")


def log_ai_task(task_name):
    """
    Decorator to automatically log AI task completion
    
    Usage:
        @log_ai_task('risk_scoring')
        def score_health_risk(records):
            # Task implementation
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            model_name = kwargs.get('model_name') or 'unknown'
            start_time = time.time()
            error = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                response_time_ms = (time.time() - start_time) * 1000
                
                AIModelLogger.log_task_completion(
                    model_name=model_name,
                    task=task_name,
                    success=True,
                    response_time_ms=response_time_ms,
                    data={'function': func.__name__}
                )
                
                return result
                
            except Exception as e:
                response_time_ms = (time.time() - start_time) * 1000
                error = str(e)
                
                AIModelLogger.log_task_completion(
                    model_name=model_name,
                    task=task_name,
                    success=False,
                    response_time_ms=response_time_ms,
                    error=error,
                    data={'function': func.__name__}
                )
                
                raise
        
        return wrapper
    return decorator


# ============================================================================
# USAGE STATISTICS HELPER
# ============================================================================

def get_model_statistics():
    """
    Get statistics about AI model usage
    
    Returns:
        dict: Model usage stats with success rates and response times
    """
    try:
        logs = IngestionLog.query.all()
        
        model_stats = {}
        
        for log in logs:
            provider = log.api_source
            details = log.details or {}
            model = details.get('model', 'unknown')
            task = details.get('task', 'unknown')
            
            key = f"{provider}:{model}"
            
            if key not in model_stats:
                model_stats[key] = {
                    'provider': provider,
                    'model': model,
                    'tasks': {},
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_response_time_ms': 0,
                    'avg_response_time_ms': 0
                }
            
            model_stats[key]['total_calls'] += 1
            
            if log.status == 'success':
                model_stats[key]['successful_calls'] += 1
            else:
                model_stats[key]['failed_calls'] += 1
            
            if log.execution_time:
                model_stats[key]['total_response_time_ms'] += log.execution_time * 1000
            
            # Track per-task stats
            if task not in model_stats[key]['tasks']:
                model_stats[key]['tasks'][task] = {
                    'calls': 0,
                    'successes': 0,
                    'failures': 0
                }
            
            model_stats[key]['tasks'][task]['calls'] += 1
            if log.status == 'success':
                model_stats[key]['tasks'][task]['successes'] += 1
            else:
                model_stats[key]['tasks'][task]['failures'] += 1
        
        # Calculate averages
        for key, stats in model_stats.items():
            if stats['total_calls'] > 0:
                stats['success_rate'] = round((stats['successful_calls'] / stats['total_calls']) * 100, 1)
                stats['avg_response_time_ms'] = round(stats['total_response_time_ms'] / stats['total_calls'], 2)
            else:
                stats['success_rate'] = 0
                stats['avg_response_time_ms'] = 0
        
        return model_stats
        
    except Exception as e:
        logger.error(f"Error getting model statistics: {str(e)}")
        return {}


# ============================================================================
# EXAMPLE USAGE IN OTHER MODULES
# ============================================================================

"""
# In services/risk_scoring.py:

from services.ai_model_logger import AIModelLogger, log_ai_task

@log_ai_task('risk_scoring')
def calculate_health_risk(records, model_name='gpt-3.5-turbo'):
    # Implementation
    return result

# Or manually:
def calculate_health_risk_manual(records):
    start = time.time()
    try:
        # Task implementation
        result = ...
        response_time = (time.time() - start) * 1000
        
        AIModelLogger.log_task_completion(
            model_name='gpt-4',
            task='risk_scoring',
            success=True,
            response_time_ms=response_time
        )
        return result
    except Exception as e:
        response_time = (time.time() - start) * 1000
        AIModelLogger.log_task_completion(
            model_name='gpt-4',
            task='risk_scoring',
            success=False,
            response_time_ms=response_time,
            error=str(e)
        )
        raise
"""
