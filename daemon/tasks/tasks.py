import random
import json
import redis
from celery import shared_task, current_task

# Import configuration
import os
import sys
import json
from pathlib import Path

# Load config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config.json')
with open(CONFIG_FILE) as config_file:
    CONFIG = json.load(config_file)

# Redis configuration
REDIS_HOST = CONFIG['redis']['host']
REDIS_PORT = CONFIG['redis']['port']
REDIS_RESULTS_QUEUE = CONFIG['redis']['channels']['results_queue']


@shared_task
def generate_random_number(user_id, min_value=1, max_value=100):
    """
    Example task that generates a random number.
    The result is published to Redis, which will be picked up by Django's consumers
    and forwarded to the client via WebSockets.
    """
    # Generate random number
    result = random.randint(min_value, max_value)
    
    # Get task ID from Celery
    task_id = current_task.request.id
    
    # Prepare result data
    result_data = {
        "user_id": user_id,
        "task_id": task_id,
        "task_type": "generate_random_number",
        "status": "completed",
        "result": {"number": result}
    }
    
    # Publish result to Redis
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )
    
    redis_client.publish(
        REDIS_RESULTS_QUEUE,
        json.dumps(result_data)
    )
    
    # Return result (this will be stored in Celery's result backend)
    return {
        'task_id': task_id,
        'user_id': user_id,
        'result': result
    }

@shared_task
def reverse_string(user_id, text):
    """
    Example task that reverses a given string.
    The result is published to Redis, which will be picked up by Django's consumers
    and forwarded to the client via WebSockets.
    """
    # Reverse the string
    result = text[::-1]
    
    # Get task ID from Celery
    task_id = current_task.request.id
    
    # Prepare result data
    result_data = {
        "user_id": user_id,
        "task_id": task_id,
        "task_type": "reverse_string",
        "status": "completed",
        "result": {"reversed_text": result}
    }
    
    # Publish result to Redis
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )
    
    redis_client.publish(
        REDIS_RESULTS_QUEUE,
        json.dumps(result_data)
    )
    
    # Return result (this will be stored in Celery's result backend)
    return {
        'task_id': task_id,
        'user_id': user_id,
        'result': result
    }
