# Simple reexport of the app from tasks.tasks
import os
import sys

# Add the daemon directory to the Python path
daemon_dir = os.path.dirname(os.path.abspath(__file__))
if daemon_dir not in sys.path:
    sys.path.insert(0, daemon_dir)

# Import the app from tasks.tasks
from tasks.tasks import app

# Print available tasks for debugging
print("Available tasks:")
print(app.tasks.keys())
