# Daemon Service

This directory contains the task processor daemon for the event-driven architecture.

## Overview

The daemon is responsible for:
- Listening to Redis channels for task requests
- Processing and validating the requests
- Dispatching Celery tasks
- Handling errors and sending notifications

## Components

- `processor.py`: Main entry point and task processor logic
- `tasks/`: Contains Celery task definitions
  - `tasks.py`: Example tasks (generate_random_number, reverse_string)
- `utils/`: Utility functions and modules
  - `config.py`: Configuration manager that loads from config.json
  - `redis_client.py`: Redis client wrapper for pub/sub operations

## Setup and Running

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Start the task processor daemon:
```
python processor.py
```

3. Start Celery workers (in a separate terminal):
```
celery -A daemon.tasks.tasks worker --loglevel=info
```

> **Important**: Both the daemon and Celery workers need to be running simultaneously. The daemon dispatches tasks to Celery, and the Celery workers execute them.

## Configuration

The daemon uses the main project's `config.json` file for configuration. 
You can override Redis settings with environment variables:

- `REDIS_HOST`: Override Redis host
- `REDIS_PORT`: Override Redis port

## Adding New Tasks

To add a new task:
1. Add the task function to `tasks/tasks.py`
2. Add task processing logic to the `process_message` method in `processor.py`

## Architecture

This daemon follows a task dispatch architecture:

1. **Redis PubSub**: The frontend/backend applications publish task requests to Redis channels
2. **Daemon Processor**: This daemon subscribes to these channels and validates incoming requests
3. **Celery Dispatch**: The daemon dispatches validated tasks to Celery
4. **Celery Workers**: Separate Celery worker processes execute the tasks asynchronously
5. **Result Publishing**: Tasks publish their results back to Redis when completed

![Daemon Architecture](https://mermaid.ink/img/pako:eNp1kMFqwzAQRH9F7CkFQ_-QSw4hkEMPgdKcRF0sa4mRtBKrCsH035tiJ5BDL2J35s3MqgcY0TEkYI_34EobdBaD8rgENqHqo_e4NvsKOrzRxC1JprTTEQfzvNmI9Vpskd01Vf_9SIEruxKJLhVZXKblXTbr_J7_nWZL_scpn4XFJ9WzUmKez3Z_CNgRFUxQYQBkEENtzr6jnl0IUlCnnoUZ6MpjS4E6lGYqktRuHQyohbJpDQn0JlrqOZLlAD2p9EAHc7VelfsOSaKH-PELi8ppRA?type=png)

## How Tasks Work

1. **Task Definition**: Tasks are defined in `tasks/tasks.py` using the Celery `@app.task` decorator
2. **Dispatching**: The daemon dispatches tasks using the `.delay()` method
3. **Execution**: Celery workers execute the tasks asynchronously
4. **Result Publishing**: Tasks publish their results to Redis using the `RedisClient`

## Using VS Code Tasks

This project includes VS Code tasks for starting the various services:

1. **Start Task Processor Daemon**: Starts this daemon
2. **Start Celery Worker**: Starts the Celery worker for the Django backend
3. **Start Redis**: Starts the Redis server
4. **Start All Services**: Starts all components together

You can run these tasks from the VS Code command palette (Ctrl+Shift+P) by searching for "Tasks: Run Task".
