import os
import json
import importlib
import logging
import redis
import traceback
import sys
import time
from celery import Celery
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load config
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config.json')
logger.info(f"Loading config from: {CONFIG_FILE}")

try:
    with open(CONFIG_FILE) as config_file:
        CONFIG = json.load(config_file)
    logger.info(f"Config loaded successfully: {CONFIG}")
except Exception as e:
    logger.error(f"Failed to load config: {e}")
    raise

# Redis configuration
REDIS_HOST = CONFIG['redis']['host']
REDIS_PORT = CONFIG['redis']['port']
REDIS_TASKS_QUEUE = CONFIG['redis']['channels']['tasks_queue']
REDIS_RESULTS_QUEUE = CONFIG['redis']['channels']['results_queue']

logger.info(f"Redis configuration: host={REDIS_HOST}, port={REDIS_PORT}")
logger.info(f"Redis channels: tasks={REDIS_TASKS_QUEUE}, results={REDIS_RESULTS_QUEUE}")

# Ensure tasks directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
logger.info(f"Tasks directory added to path: {os.path.dirname(os.path.abspath(__file__))}")

# Import the tasks directly - they have their own Celery app configured
from tasks.tasks import generate_random_number, reverse_string
logger.info("Tasks imported: generate_random_number, reverse_string")


class TaskProcessor:
    """
    Process tasks received from Redis and send them to Celery.
    
    This class acts as a bridge between the Redis pub/sub system and Celery.
    It listens for task messages from the frontend (via Django API),
    and forwards them to the appropriate Celery task.
    """
    def __init__(self):
        logger.info("Initializing TaskProcessor...")
        
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
            logger.info(f"Redis client created for {REDIS_HOST}:{REDIS_PORT}")
            
            # Test Redis connection
            self.test_redis_connection()
            
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe(REDIS_TASKS_QUEUE)
            logger.info(f"Subscribed to Redis channel: {REDIS_TASKS_QUEUE}")
            
            # Print available tasks
            self.list_available_tasks()
        except Exception as e:
            logger.error(f"Error initializing TaskProcessor: {e}")
            traceback.print_exc()
            raise
    
    def test_redis_connection(self):
        """Test if Redis connection is working properly"""
        test_key = "processor_test_key"
        test_value = "processor_test_value"
        
        # Test SET
        self.redis_client.set(test_key, test_value)
        logger.info(f"Set Redis test key: {test_key}")
        
        # Test GET
        result = self.redis_client.get(test_key)
        logger.info(f"Got Redis test value: {result}")
        
        # Clean up
        self.redis_client.delete(test_key)
        logger.info(f"Deleted Redis test key: {test_key}")
        
        # Test PUB/SUB with a simple message
        test_message = {"test": "message"}
        result = self.redis_client.publish(REDIS_TASKS_QUEUE, json.dumps(test_message))
        logger.info(f"Published test message to {REDIS_TASKS_QUEUE}, result: {result}")
    
    def list_available_tasks(self):
        """List all available Celery tasks"""
        try:
            task_module = importlib.import_module('tasks.tasks')
            tasks = [name for name in dir(task_module) 
                    if callable(getattr(task_module, name)) and not name.startswith('_')]
            logger.info(f"Available tasks: {tasks}")
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
    
    def process_message(self, message):
        """Process a message from Redis and dispatch to Celery"""
        if message['type'] == 'message':
            logger.info(f"Processing message: {message}")
            try:
                # Parse the message
                data = json.loads(message['data'])
                user_id = data.get('user_id')
                task_type = data.get('task_type')
                parameters = data.get('parameters', {})
                
                logger.info(f"Received task: {task_type} (User: {user_id}, Parameters: {parameters})")
                
                if not task_type or not user_id:
                    logger.error(f"Missing required task data: task_type={task_type}, user_id={user_id}")
                    return
                
                # Get the task function from the registry
                try:
                    # Dynamic task resolution based on task type
                    if task_type == 'generate_random_number':
                        min_value = parameters.get('min_value', 1)
                        max_value = parameters.get('max_value', 100)
                        
                        # IMPORTANT: Import task dynamically to ensure it's registered properly
                        from tasks.tasks import generate_random_number
                        
                        logger.info(f"Calling generate_random_number({user_id}, {min_value}, {max_value})")
                        
                        # Dispatch task directly
                        task = generate_random_number.delay(user_id, min_value, max_value)
                        
                        logger.info(f"Task dispatched with ID: {task.id}")
                        
                        # Debug: publish a test message directly to results queue
                        debug_result = {
                            "user_id": user_id,
                            "task_id": "debug-pre-task",
                            "task_type": "debug",
                            "status": "debug",
                            "message": f"Task {task_type} dispatched with ID {task.id}"
                        }
                        self.redis_client.publish(REDIS_RESULTS_QUEUE, json.dumps(debug_result))
                        logger.info("Published debug confirmation to results queue")
                        
                    elif task_type == 'reverse_string':
                        text = parameters.get('text', '')
                        
                        if not text:
                            logger.error("Missing text for reverse_string task")
                            return
                            
                        # IMPORTANT: Import task dynamically to ensure it's registered properly
                        from tasks.tasks import reverse_string
                        
                        logger.info(f"Calling reverse_string({user_id}, {text})")
                        
                        # Dispatch task directly
                        task = reverse_string.delay(user_id, text)
                        
                        logger.info(f"Task dispatched with ID: {task.id}")
                    else:
                        logger.warning(f"Unknown task type: {task_type}")
                        
                        # Publish error back to results queue
                        error_data = {
                            "user_id": user_id,
                            "task_id": "error",
                            "task_type": task_type,
                            "status": "error",
                            "error": f"Task type not found: {task_type}"
                        }
                        self.redis_client.publish(REDIS_RESULTS_QUEUE, json.dumps(error_data))
                        logger.info(f"Published error message to {REDIS_RESULTS_QUEUE}")
                except Exception as e:
                    error_msg = f"Error executing task function: {e}"
                    logger.error(error_msg, exc_info=True)
                    
                    # Publish error back to results queue
                    if user_id:
                        error_data = {
                            "user_id": user_id,
                            "task_id": "error",
                            "task_type": task_type if task_type else "unknown",
                            "status": "error",
                            "error": error_msg
                        }
                        self.redis_client.publish(REDIS_RESULTS_QUEUE, json.dumps(error_data))
                        logger.info(f"Published error message to {REDIS_RESULTS_QUEUE}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in message: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    
    def run(self):
        """Run the task processor"""
        logger.info("Task processor started")
        logger.info(f"Listening for tasks on Redis channel: {REDIS_TASKS_QUEUE}")
        try:
            for message in self.pubsub.listen():
                self.process_message(message)
        except KeyboardInterrupt:
            logger.info("Task processor shutting down")
        except Exception as e:
            logger.error(f"Error in processor main loop: {e}", exc_info=True)
            raise


if __name__ == '__main__':
    try:
        logger.info("Starting task processor...")
        processor = TaskProcessor()
        processor.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
