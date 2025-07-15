"""
Configuration loader for the daemon processor.
Handles reading from config.json and provides environment-specific overrides.
"""
import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the daemon processor"""
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance exists"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from JSON file"""
        # Find the project root (where config.json is located)
        project_root = Path(__file__).resolve().parent.parent.parent
        config_file = project_root / 'config.json'
        
        logger.info(f"Loading config from: {config_file}")
        
        try:
            with open(config_file) as f:
                self._config = json.load(f)
            logger.info(f"Config loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
        
        # Apply any environment variable overrides
        self._apply_env_overrides()
    
    def _apply_env_overrides(self):
        """Override configuration with environment variables if available"""
        # Redis host and port can be overridden with environment variables
        if os.environ.get('REDIS_HOST'):
            self._config['redis']['host'] = os.environ.get('REDIS_HOST')
            logger.info(f"Overrode Redis host from environment: {self._config['redis']['host']}")
            
        if os.environ.get('REDIS_PORT'):
            try:
                self._config['redis']['port'] = int(os.environ.get('REDIS_PORT'))
                logger.info(f"Overrode Redis port from environment: {self._config['redis']['port']}")
            except ValueError:
                logger.warning(f"Invalid REDIS_PORT environment variable: {os.environ.get('REDIS_PORT')}")
    
    @property
    def redis_host(self):
        """Get Redis host"""
        return self._config['redis']['host']
    
    @property
    def redis_port(self):
        """Get Redis port"""
        return self._config['redis']['port']
    
    @property
    def redis_tasks_channel(self):
        """Get Redis tasks queue channel name"""
        return self._config['redis']['channels']['tasks_queue']
    
    @property
    def redis_results_channel(self):
        """Get Redis results queue channel name"""
        return self._config['redis']['channels']['results_queue']
    
    @property
    def celery_broker_url(self):
        """Get Celery broker URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    @property
    def celery_result_backend(self):
        """Get Celery result backend URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    def get_full_config(self):
        """Get the entire configuration dictionary"""
        return self._config


# Create a singleton instance for easy import
config = Config()
