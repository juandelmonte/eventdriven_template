# Celery configuration
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'

# Task serialization
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'

# Task result settings
task_ignore_result = False
task_store_errors_even_if_ignored = True

# Time limits
task_time_limit = 300  # 5 minutes
task_soft_time_limit = 240  # 4 minutes

# Concurrency and prefetch
worker_prefetch_multiplier = 1
worker_concurrency = 8  # Adjust based on CPU cores

# Logging
worker_log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
worker_task_log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Import tasks from modules - This is the relative import path from where celery worker is run
imports = ('daemon.tasks.tasks',)

# Task routes - using both possible import paths to be safe
task_routes = {
    'tasks.tasks.*': {'queue': 'celery'},
    'daemon.tasks.tasks.*': {'queue': 'celery'},
}

# Enable task events for monitoring
worker_send_task_events = True
task_send_sent_event = True
