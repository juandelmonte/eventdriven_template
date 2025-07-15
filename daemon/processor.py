"""
Main task processor for the event-driven architecture.

This module subscribes to Redis channels for incoming task requests,
processes them, and dispatches the appropriate Celery tasks.
"""
import json
import logging
import traceback
import importlib
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import utils and tasks
from daemon.utils.redis_client import RedisClient
from daemon.utils.config import config
from daemon.tasks.tasks import generate_random_number, reverse_string

class TaskProcessor:
    """
    Process tasks received from Redis and send them to Celery.
    
    This class acts as a bridge between the Redis pub/sub system and Celery.
    It listens for task messages from the frontend (via Django API),
    and forwards them to the appropriate Celery task.
    """
    def __init__(self):
        """Initialize the task processor with Redis connection"""
        logger.info("Initializing TaskProcessor...")
        
        try:
            # Create Redis client
            self.redis_client = RedisClient()
            self.pubsub = self.redis_client.create_pubsub()
            
            # Print available tasks
            self.list_available_tasks()
        except Exception as e:
            logger.error(f"Error initializing TaskProcessor: {e}")
            traceback.print_exc()
            raise
    
    def list_available_tasks(self):
        """List all available Celery tasks"""
        try:
            # Get tasks module
            task_module = importlib.import_module('daemon.tasks.tasks')
            
            # Find all callable functions that don't start with _
            tasks = [name for name in dir(task_module) 
                    if callable(getattr(task_module, name)) and not name.startswith('_')]
            
            # Filter out non-task functions
            tasks = [name for name in tasks if hasattr(getattr(task_module, name), 'delay')]
            
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
                
                # Process task based on type
                if task_type == 'generate_random_number':
                    min_value = parameters.get('min_value', 1)
                    max_value = parameters.get('max_value', 100)
                    
                    logger.info(f"Dispatching generate_random_number({user_id}, {min_value}, {max_value})")
                    
                    # Dispatch task
                    task = generate_random_number.delay(user_id, min_value, max_value)
                    logger.info(f"Task dispatched with ID: {task.id}")
                    
                elif task_type == 'reverse_string':
                    text = parameters.get('text', '')
                    
                    if not text:
                        logger.error("Missing text for reverse_string task")
                        # Publish error
                        self.redis_client.publish_error(
                            user_id=user_id,
                            task_type=task_type,
                            error_message="Missing 'text' parameter"
                        )
                        return
                    
                    logger.info(f"Dispatching reverse_string({user_id}, {text})")
                    
                    # Dispatch task
                    task = reverse_string.delay(user_id, text)
                    logger.info(f"Task dispatched with ID: {task.id}")
                    
                else:
                    logger.warning(f"Unknown task type: {task_type}")
                    
                    # Publish error
                    self.redis_client.publish_error(
                        user_id=user_id,
                        task_type=task_type,
                        error_message=f"Task type not found: {task_type}"
                    )
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in message: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    
    def run(self):
        """Run the task processor"""
        logger.info("Task processor started")
        logger.info(f"Listening for tasks on Redis channel: {config.redis_tasks_channel}")
        
        try:
            # Listen for messages
            for message in self.pubsub.listen():
                self.process_message(message)
        except KeyboardInterrupt:
            logger.info("Task processor shutting down")
        except Exception as e:
            logger.error(f"Error in processor main loop: {e}", exc_info=True)
            raise


def main():
    """Main entry point for the daemon"""
    try:
        logger.info("Starting task processor...")
        processor = TaskProcessor()
        processor.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
