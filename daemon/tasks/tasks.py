"""
Celery task definitions for the daemon.

This module defines all the async tasks that can be executed by Celery.
These tasks are imported and executed by the processor.py module.
"""
import json
import random
import datetime
import logging
from celery import Celery, current_task
from ..utils.config import config
from ..utils.redis_client import RedisClient

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = RedisClient()

# Initialize Celery app with config
app = Celery('tasks')
app.conf.update(
    broker_url=config.celery_broker_url,
    result_backend=config.celery_result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
)
logger.info("Celery app initialized")

@app.task
def generate_random_number(user_id, min_value=1, max_value=100):
    """
    Example task that generates a random number.
    
    Args:
        user_id (str): User ID for the task
        min_value (int): Minimum value for the random number
        max_value (int): Maximum value for the random number
        
    Returns:
        dict: Task result with user_id, task_id, and result
    """
    logger.info(f"TASK START: generate_random_number for user {user_id}")
    logger.info(f"Parameters: min_value={min_value}, max_value={max_value}")
    
    try:
        # Generate random number
        result = random.randint(int(min_value), int(max_value))
        logger.info(f"Generated random number: {result}")
        
        # Get task ID from Celery
        task_id = current_task.request.id
        
        # Publish result to Redis
        redis_client.publish_task_result(
            user_id=user_id,
            task_id=task_id,
            task_type="generate_random_number",
            result={"number": result}
        )
        
        # Return result (stored in Celery's result backend)
        return {
            'task_id': task_id,
            'user_id': user_id,
            'result': result
        }
    except Exception as e:
        logger.error(f"Error in generate_random_number task: {e}", exc_info=True)
        
        # Publish error to Redis
        try:
            redis_client.publish_error(
                user_id=user_id,
                task_type="generate_random_number",
                error_message=str(e),
                task_id=current_task.request.id
            )
        except Exception as redis_error:
            logger.error(f"Failed to publish error to Redis: {redis_error}")
        
        # Re-raise the exception
        raise

@app.task
def reverse_string(user_id, text):
    """
    Example task that reverses a string.
    
    Args:
        user_id (str): User ID for the task
        text (str): Text to reverse
        
    Returns:
        dict: Task result with user_id, task_id, and result
    """
    logger.info(f"TASK START: reverse_string for user {user_id}")
    logger.info(f"Text to reverse: {text}")
    
    try:
        # Simple string reversal
        result = text[::-1]
        logger.info(f"Reversed text: {result}")
        
        # Get task ID from Celery
        task_id = current_task.request.id
        
        # Publish result to Redis
        redis_client.publish_task_result(
            user_id=user_id,
            task_id=task_id,
            task_type="reverse_string",
            result={"reversed_text": result}
        )
        
        # Return result (stored in Celery's result backend)
        return {
            'task_id': task_id,
            'user_id': user_id,
            'result': result
        }
    except Exception as e:
        logger.error(f"Error in reverse_string task: {e}", exc_info=True)
        
        # Publish error to Redis
        try:
            redis_client.publish_error(
                user_id=user_id,
                task_type="reverse_string",
                error_message=str(e),
                task_id=current_task.request.id
            )
        except Exception as redis_error:
            logger.error(f"Failed to publish error to Redis: {redis_error}")
        
        # Re-raise the exception
        raise

# Print when module is loaded
logger.info("Tasks module loaded and tasks registered with Celery")
