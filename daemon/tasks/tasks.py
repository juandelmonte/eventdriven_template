import random
import json
import redis
import datetime  # Added missing import for datetime
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
    print(f"TASK: generate_random_number for user {user_id}")
    print(f"Redis config: host={REDIS_HOST}, port={REDIS_PORT}, queue={REDIS_RESULTS_QUEUE}")
    
    # Generate random number
    result = random.randint(min_value, max_value)
    print(f"Generated random number: {result}")
    
    # Get task ID from Celery
    task_id = current_task.request.id
    print(f"Task ID: {task_id}")
    
    # Prepare result data
    result_data = {
        "user_id": user_id,
        "task_id": task_id,
        "task_type": "generate_random_number",
        "status": "completed",
        "result": {"number": result},
        "timestamp": str(datetime.datetime.now())
    }
    
    print(f"Publishing result to Redis: {result_data}")
    
    # Publish result to Redis
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        
        pub_result = redis_client.publish(
            REDIS_RESULTS_QUEUE,
            json.dumps(result_data)
        )
        
        print(f"Redis publish result: {pub_result}")
    except Exception as e:
        print(f"Error publishing to Redis: {str(e)}")
        import traceback
        traceback.print_exc()
    
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
