# Event-Driven Architecture Template

This project demonstrates an event-driven architecture using React, Django, Redis, and Celery. It allows users to submit tasks from a React frontend, which are then processed asynchronously by Celery workers, with results sent back to the frontend via WebSockets.

## Architecture Overview

The architecture consists of three main components with clear separation of concerns:

1. **Frontend (React)**: Provides the user interface to submit tasks and view results.
2. **Backend (Django)**: Handles HTTP requests, authentication, and WebSocket connections. Acts as a message passing service only.
3. **Daemon (Celery)**: Processes tasks asynchronously and publishes results.

The components communicate through Redis:
- Frontend → Backend: HTTP requests to submit tasks
- Backend → Daemon: Redis publish/subscribe to forward task requests
- Daemon → Frontend: Results sent via Redis and WebSockets

This architecture is designed for high concurrency:
- No database storage of tasks (uses Celery's result backend)
- All task processing logic is in the daemon, not in Django
- Event-driven communication via Redis pub/sub
- Real-time updates via WebSockets

## Generic Task System

The application uses a generic task dispatching system that allows new task types to be added without creating new API endpoints. The system consists of:

1. **Task Registry**: Maps task types to their serializers for validation
2. **Generic Task Dispatcher**: A single API endpoint that routes tasks based on task type
3. **Dynamic Task Import**: The daemon dynamically imports and runs tasks by name
4. **WebSocket Results**: All task results are delivered via WebSockets

This design makes the application highly extensible - you can add new task types with minimal changes.

## Project Structure

```
eventdriven_template/
│
├── config.json            # Global configuration file
│
├── backend/               # Django backend
│   ├── requirements.txt   # Python dependencies for backend
│   └── djangoproject/     # Django project
│       ├── manage.py
│       ├── djangoproject/ # Django project settings
│       ├── users/         # User authentication app
│       └── tasks/         # Tasks app for handling task requests
│
├── daemon/                # Celery worker daemon
│   ├── requirements.txt   # Python dependencies for daemon
│   ├── processor.py       # Task processor that listens to Redis
│   └── tasks/             # Task definitions
│
└── frontend/              # React frontend
    ├── requirements.txt   # Node.js dependencies for frontend
    └── reactproject/      # React project
        ├── package.json
        └── src/           # React source code
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- Redis server

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd eventdriven_template
```

2. **Set up the backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd djangoproject
python manage.py migrate
python manage.py createsuperuser
```

3. **Set up the daemon**

```bash
cd daemon
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Set up the frontend**

```bash
cd frontend/reactproject
npm install axios react-router-dom jwt-decode socket.io-client
```

### Running the Application

1. **Start Redis server**

```bash
redis-server
```

2. **Start Django backend**

```bash
cd backend/djangoproject
python manage.py runserver
```

3. **Start Celery worker**

```bash
cd backend/djangoproject
celery -A djangoproject worker --loglevel=info
```

4. **Start task processor daemon**

```bash
cd daemon
python processor.py
```

5. **Start React frontend**

```bash
cd frontend/reactproject
npm start
```

The application will be available at http://localhost:3000

## Using the System

### Authentication

1. Register a new user account at `/register`
2. Log in with your credentials at `/login`
3. You'll be redirected to the dashboard after successful login

### Creating and Running Tasks

#### Example: Random Number Generation

1. On the dashboard, you'll find a form to generate a random number
2. Enter the minimum and maximum values
3. Click "Generate Random Number"

This will:
1. Send an HTTP request to the Django backend
2. Django will create a task record and publish a message to Redis
3. The daemon will pick up the message and send it to Celery
4. Celery will process the task
5. The result will be updated in the database
6. A WebSocket notification will be sent to the frontend
7. The frontend will update the UI with the result

## Creating Custom Tasks

To create custom tasks, follow these steps:

### 1. Define the task in the Daemon

In `daemon/tasks/tasks.py`:

```python
@shared_task
def my_custom_task(user_id, param1, param2):
    """
    Example custom task
    """
    # Perform the task
    result = perform_operation(param1, param2)
    
    # Get task ID from Celery
    task_id = current_task.request.id
    
    # Prepare result data
    result_data = {
        "user_id": user_id,
        "task_id": task_id,
        "task_type": "my_custom_task",
        "status": "completed",
        "result": {"data": result}
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
    
    # Return result (stored in Celery's result backend)
    return {
        'task_id': task_id,
        'user_id': user_id,
        'result': result
    }
```

### 2. Update the daemon processor

In `daemon/processor.py`, update the `process_message` method:

```python
def process_message(self, message):
    if message['type'] == 'message':
        try:
            data = json.loads(message['data'])
            user_id = data.get('user_id')
            task_type = data.get('task_type')
            parameters = data.get('parameters', {})
            
            logger.info(f"Received task: {task_type} (User: {user_id})")
            
            # Process based on task type
            if task_type == 'generate_random_number':
                # Existing task logic
            elif task_type == 'my_custom_task':
                from tasks.tasks import my_custom_task
                task = my_custom_task.apply_async(
                    args=[user_id],
                    kwargs={
                        'param1': parameters.get('param1'),
                        'param2': parameters.get('param2')
                    }
                )
                logger.info(f"Task {task.id} sent to Celery")
            else:
                logger.warning(f"Unknown task type: {task_type}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
```

### 3. Create an API endpoint in Django

In `backend/djangoproject/tasks/views.py`:

```python
class MyCustomTaskView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=MyCustomTaskSerializer,
        responses={
            202: OpenApiResponse(
                response=TaskResponseSerializer,
                description="Task successfully submitted"
            ),
            400: OpenApiResponse(description="Bad request")
        },
        description="Submit a custom task",
    )
    def post(self, request, *args, **kwargs):
        serializer = MyCustomTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create a task message
        task_data = {
            "user_id": request.user.id,
            "task_type": "my_custom_task",
            "parameters": {
                "param1": serializer.validated_data.get('param1'),
                "param2": serializer.validated_data.get('param2')
            }
        }
        
        # Send task to Redis queue
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        
        # Publish to Redis tasks queue
        redis_client.publish(
            settings.REDIS_TASKS_QUEUE,
            json.dumps(task_data)
        )
        
        # Return a response with task info
        return Response({
            'task_id': 'pending',
            'task_type': 'my_custom_task',
            'status': 'submitted'
        }, status=status.HTTP_202_ACCEPTED)
```

### 4. Add the API endpoint to the URL configuration

In `backend/djangoproject/tasks/urls.py`:

```python
urlpatterns = [
    # Existing patterns
    path('my-custom-task/', MyCustomTaskView.as_view(), name='my-custom-task'),
]
```

### 5. Create a service function in the React frontend

In `frontend/reactproject/src/services/api.js`:

```javascript
// Add to taskService
myCustomTask: async (param1, param2) => {
  const response = await apiClient.post('/tasks/my-custom-task/', { 
    param1, param2 
  });
  return response.data;
}
```

### 6. Create a UI component in React

In `frontend/reactproject/src/components/MyCustomTaskForm.js`:

```javascript
import React, { useState } from 'react';
import { taskService } from '../services/api';

const MyCustomTaskForm = () => {
  const [param1, setParam1] = useState('');
  const [param2, setParam2] = useState('');
  const [processing, setProcessing] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setProcessing(true);
    
    try {
      await taskService.myCustomTask(param1, param2);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setProcessing(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={processing}>
        {processing ? 'Processing...' : 'Submit Task'}
      </button>
    </form>
  );
};

export default MyCustomTaskForm;
```

## Adding New Tasks

Adding a new task type is simple and requires minimal changes:

1. **Create a serializer** in `backend/djangoproject/tasks/serializers.py`:
```python
class MyNewTaskSerializer(serializers.Serializer):
    param1 = serializers.CharField(max_length=100)
    param2 = serializers.IntegerField(default=10)
```

2. **Add the task to the registry** in `backend/djangoproject/tasks/views.py`:
```python
# Task registry - maps task_type to serializer class
TASK_SERIALIZERS = {
    'generate_random_number': GenerateRandomNumberSerializer,
    'reverse_string': ReverseStringSerializer,
    'my_new_task': MyNewTaskSerializer,  # Add your new task here
}

# List of available tasks with descriptions
AVAILABLE_TASKS = {
    'generate_random_number': 'Generate a random number between a min and max value',
    'reverse_string': 'Reverse a given text string',
    'my_new_task': 'Description of my new task',  # Add description here
}
```

3. **Implement the task function** in `daemon/tasks/tasks.py`:
```python
@shared_task
def my_new_task(user_id, param1, param2=10):
    """
    Example of a new task
    """
    # Your task implementation
    result = f"{param1} processed with param2={param2}"
    
    # Get task ID from Celery
    task_id = current_task.request.id
    
    # Prepare result data
    result_data = {
        "user_id": user_id,
        "task_id": task_id,
        "task_type": "my_new_task",
        "status": "completed",
        "result": {"output": result}
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
    
    return {
        'task_id': task_id,
        'user_id': user_id,
        'result': result
    }
```

4. **Import the new task** in `daemon/processor.py`:
```python
from tasks.tasks import generate_random_number, reverse_string, my_new_task
```

5. **Add a convenience method** in the frontend API service (optional):
```javascript
// Convenience method for the new task
myNewTask: async (param1, param2=10) => {
  return taskService.submitTask('my_new_task', { param1, param2 });
},
```

That's it! Your new task will now be available at `/api/tasks/my_new_task/` and listed in the task info endpoint at `/api/tasks/`.

## License

[MIT License](LICENSE)
