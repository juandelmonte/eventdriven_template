# This file marks the directory as a Python package
# and helps with imports and Celery task registration

# Explicitly import task modules to ensure they're discovered
from . import tasks
