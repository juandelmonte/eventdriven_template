"""
Redis client wrapper for the daemon processor.
Handles connection and pub/sub operations.
"""
import json
import logging
import redis
from .config import config

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper with connection management and pub/sub capabilities"""
    
    def __init__(self, host=None, port=None, decode_responses=True):
        """Initialize Redis client with config or explicit connection details"""
        self.host = host or config.redis_host
        self.port = port or config.redis_port
        self.decode_responses = decode_responses
        self.tasks_channel = config.redis_tasks_channel
        self.results_channel = config.redis_results_channel
        self._client = None
        self._pubsub = None
        
        # Create Redis client
        self._connect()
    
    def _connect(self):
        """Establish connection to Redis server"""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=self.decode_responses
            )
            logger.info(f"Redis client created for {self.host}:{self.port}")
            
            # Test connection
            self.test_connection()
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def test_connection(self):
        """Test if Redis connection is working properly"""
        test_key = "daemon_test_key"
        test_value = "daemon_test_value"
        
        # Test SET
        self._client.set(test_key, test_value)
        
        # Test GET
        result = self._client.get(test_key)
        
        # Clean up
        self._client.delete(test_key)
        
        if result != test_value:
            raise ConnectionError(f"Redis test failed. Expected {test_value}, got {result}")
        
        logger.info("Redis connection test successful")
    
    def publish_task_result(self, user_id, task_id, task_type, result=None, status="completed", error=None):
        """Publish task results to Redis"""
        result_data = {
            "user_id": user_id,
            "task_id": task_id,
            "task_type": task_type,
            "status": status,
            "timestamp": import_datetime_from_function(),  # Using helper function
        }
        
        # Add result or error based on status
        if status == "completed" and result is not None:
            result_data["result"] = result
        elif status == "error" and error is not None:
            result_data["error"] = error
        
        # Publish to Redis
        try:
            publish_result = self._client.publish(
                self.results_channel,
                json.dumps(result_data)
            )
            logger.info(f"Published result to {self.results_channel}: {publish_result}")
            return publish_result
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
            raise
    
    def publish_error(self, user_id, task_type, error_message, task_id="error"):
        """Convenience method to publish error messages"""
        return self.publish_task_result(
            user_id=user_id,
            task_id=task_id,
            task_type=task_type,
            status="error",
            error=error_message
        )
    
    def create_pubsub(self):
        """Create and return a pubsub object subscribed to the tasks channel"""
        if not self._pubsub:
            self._pubsub = self._client.pubsub()
            self._pubsub.subscribe(self.tasks_channel)
            logger.info(f"Subscribed to Redis channel: {self.tasks_channel}")
        return self._pubsub
    
    def get_pubsub(self):
        """Get the current pubsub object or create a new one"""
        return self._pubsub or self.create_pubsub()


def import_datetime_from_function():
    """Helper function to import datetime and return ISO-formatted current time
    
    This prevents circular imports when the redis_client is imported at module level
    """
    import datetime
    return datetime.datetime.now().isoformat()
