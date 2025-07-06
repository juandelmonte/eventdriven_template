import os
import json
import importlib
import logging
import redis
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
with open(CONFIG_FILE) as config_file:
    CONFIG = json.load(config_file)

# Redis configuration
REDIS_HOST = CONFIG['redis']['host']
REDIS_PORT = CONFIG['redis']['port']
REDIS_TASKS_QUEUE = CONFIG['redis']['channels']['tasks_queue']
REDIS_RESULTS_QUEUE = CONFIG['redis']['channels']['results_queue']

# Celery configuration
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

# Create Celery app
app = Celery('daemon')
app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
    task_routes={
        'tasks.tasks.*': {'queue': 'default'}
    }
)

# Ensure tasks directory is in path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Register tasks
app.autodiscover_tasks(['tasks'])

# Import the task after Celery app is configured
from tasks.tasks import generate_random_number, reverse_string


class TaskProcessor:
    """
    Process tasks received from Redis and send them to Celery.
    
    This class acts as a bridge between the Redis pub/sub system and Celery.
    It listens for task messages from the frontend (via Django API),
    and forwards them to the appropriate Celery task.
    """
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe(REDIS_TASKS_QUEUE)
        logger.info(f"Subscribed to Redis channel: {REDIS_TASKS_QUEUE}")

    def process_message(self, message):
        """Process a message from Redis and dispatch to Celery"""
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                user_id = data.get('user_id')
                task_type = data.get('task_type')
                parameters = data.get('parameters', {})
                
                logger.info(f"Received task: {task_type} (User: {user_id})")
                
                # Get the task function from the registry
                try:
                    # Dynamic task resolution - get the appropriate task function based on task_type
                    task_module = importlib.import_module('tasks.tasks')
                    task_function = getattr(task_module, task_type, None)
                    
                    if task_function:
                        # Call the Celery task
                        task = task_function.apply_async(
                            args=[user_id],
                            kwargs=parameters
                        )
                        logger.info(f"Task {task.id} sent to Celery")
                    else:
                        logger.warning(f"Task function not found for task type: {task_type}")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error importing task function: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    
    def run(self):
        """Run the task processor"""
        logger.info("Task processor started")
        try:
            for message in self.pubsub.listen():
                self.process_message(message)
        except KeyboardInterrupt:
            logger.info("Task processor shutting down")


if __name__ == '__main__':
    processor = TaskProcessor()
    processor.run()
