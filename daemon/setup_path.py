"""
Helper module to set up the Python path correctly for the daemon.
This ensures that all modules can be imported correctly regardless of where the process is started.
"""
import os
import sys

# Get the parent directory (event_driven_template)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add parent directory to Python path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add daemon directory to Python path
daemon_dir = os.path.dirname(os.path.abspath(__file__))
if daemon_dir not in sys.path:
    sys.path.insert(0, daemon_dir)

# Print the Python path for debugging
print(f"Python path: {sys.path}")
