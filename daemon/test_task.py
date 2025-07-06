import sys
import os
import json
import time
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing Celery task dispatch...")

# Load config
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config.json')
print(f"Loading config from: {CONFIG_FILE}")

try:
    with open(CONFIG_FILE) as config_file:
        CONFIG = json.load(config_file)
    print(f"Config loaded successfully")
except Exception as e:
    print(f"Failed to load config: {e}")
    sys.exit(1)

# Direct task testing
try:
    print("Importing task directly...")
    from tasks.tasks import generate_random_number
    
    print("Calling generate_random_number task...")
    user_id = "test-user-123"
    min_value = 1
    max_value = 100
    
    result = generate_random_number.delay(user_id, min_value, max_value)
    print(f"Task dispatched with ID: {result.id}")
    
    # Wait for task to complete
    print("Waiting for task result...")
    for i in range(10):
        if result.ready():
            print(f"Task completed with result: {result.result}")
            break
        print(f"Waiting for task... ({i+1}/10)")
        time.sleep(1)
    
    if not result.ready():
        print("Task did not complete in time")
        
except Exception as e:
    print(f"Error testing task: {e}")
    import traceback
    traceback.print_exc()

print("Test script completed")
