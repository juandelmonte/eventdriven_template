import json
import random
import redis
import datetime
import logging
import sys
import os

# Add the parent directory to the Python path if needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from celery import Celery, shared_task, current_task

# Import configuration
from pathlib import Path
import os
import sys

# Configure logging with more detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load config from parent directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config.json')
logger.info(f"Loading config from: {CONFIG_FILE}")

try:
    with open(CONFIG_FILE) as config_file:
        CONFIG = json.load(config_file)
    logger.info(f"Task module config loaded: {CONFIG}")
except Exception as e:
    logger.error(f"Failed to load config: {e}")
    raise

# Redis configuration
REDIS_HOST = CONFIG['redis']['host']
REDIS_PORT = CONFIG['redis']['port']
REDIS_TASKS_QUEUE = CONFIG['redis']['channels']['tasks_queue']
REDIS_RESULTS_QUEUE = CONFIG['redis']['channels']['results_queue']

logger.info(f"Task module Redis config: host={REDIS_HOST}, port={REDIS_PORT}")
logger.info(f"Task module Redis queues: tasks={REDIS_TASKS_QUEUE}, results={REDIS_RESULTS_QUEUE}")

# Initialize Celery app with proper configuration
app = Celery('tasks')
app.conf.update(
    broker_url=f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
    result_backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
)
logger.info("Celery app initialized in tasks.py")

@app.task
def generate_random_number(user_id, min_value=1, max_value=100):
    """
    Example task that generates a random number.
    The result is published to Redis, which will be picked up by Django's consumers
    and forwarded to the client via WebSockets.
    """
    # Add more verbose logging
    logger.info(f"TASK START: generate_random_number for user {user_id}")
    logger.info(f"Parameters: min_value={min_value}, max_value={max_value}")
    logger.info(f"Redis settings: host={REDIS_HOST}, port={REDIS_PORT}, results_queue={REDIS_RESULTS_QUEUE}")
    
    try:
        # Generate random number
        result = random.randint(int(min_value), int(max_value))
        logger.info(f"Generated random number: {result}")
        
        # Get task ID from Celery
        task_id = current_task.request.id
        logger.info(f"Task ID: {task_id}")
        
        # Prepare result data
        result_data = {
            "user_id": user_id,
            "task_id": task_id,
            "task_type": "generate_random_number",
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "result": {"number": result}
        }
        
        logger.info(f"Publishing result to Redis: {result_data}")
        
        # Publish result to Redis
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        
        # Test Redis connection
        redis_test_key = f"test_key_{user_id}"
        redis_client.set(redis_test_key, "test_value")
        redis_client.delete(redis_test_key)
        logger.info("Redis connection test successful")
        
        # Publish to Redis results queue
        publish_result = redis_client.publish(
            REDIS_RESULTS_QUEUE,
            json.dumps(result_data)
        )
        
        logger.info(f"Redis publish result: {publish_result}")
        
        # Return result (this will be stored in Celery's result backend)
        return {
            'task_id': task_id,
            'user_id': user_id,
            'result': result
        }
    except Exception as e:
        logger.error(f"Error in generate_random_number task: {e}", exc_info=True)
        
        # Try to publish error to Redis
        try:
            error_data = {
                "user_id": user_id,
                "task_id": current_task.request.id,
                "task_type": "generate_random_number",
                "status": "error",
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e)
            }
            
            redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
            
            redis_client.publish(
                REDIS_RESULTS_QUEUE,
                json.dumps(error_data)
            )
            
            logger.info("Published error message to Redis")
        except Exception as redis_error:
            logger.error(f"Failed to publish error to Redis: {redis_error}")
        
        # Re-raise the exception
        raise

@app.task
def reverse_string(user_id, text):
    """
    Example task that reverses a string.
    The result is published to Redis, which will be picked up by Django's consumers
    and forwarded to the client via WebSockets.
    """
    logger.info(f"TASK START: reverse_string for user {user_id}")
    logger.info(f"Text to reverse: {text}")
    
    try:
        # Simple string reversal
        result = text[::-1]
        logger.info(f"Reversed text: {result}")
        
        # Get task ID from Celery
        task_id = current_task.request.id
        
        # Prepare result data
        result_data = {
            "user_id": user_id,
            "task_id": task_id,
            "task_type": "reverse_string",
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "result": {"reversed_text": result}
        }
        
        logger.info(f"Publishing result to Redis: {result_data}")
        
        # Publish result to Redis
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        
        publish_result = redis_client.publish(
            REDIS_RESULTS_QUEUE,
            json.dumps(result_data)
        )
        
        logger.info(f"Redis publish result: {publish_result}")
        
        # Return result (this will be stored in Celery's result backend)
        return {
            'task_id': task_id,
            'user_id': user_id,
            'result': result
        }
    except Exception as e:
        logger.error(f"Error in reverse_string task: {e}", exc_info=True)
        
        # Try to publish error to Redis
        try:
            error_data = {
                "user_id": user_id,
                "task_id": current_task.request.id,
                "task_type": "reverse_string",
                "status": "error",
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e)
            }
            
            redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
            
            redis_client.publish(
                REDIS_RESULTS_QUEUE,
                json.dumps(error_data)
            )
            
            logger.info("Published error message to Redis")
        except Exception as redis_error:
            logger.error(f"Failed to publish error to Redis: {redis_error}")
        
        # Re-raise the exception
        raise

# Print when module is loaded
logger.info("Tasks module loaded and tasks registered with Celery")
