from django.urls import path
from .views import TaskDispatcherView, TasksInfoView
from .diagnostic_views import websocket_diagnostics

urlpatterns = [
    # Generic task dispatcher - handles all task types
    path('<str:task_type>/', TaskDispatcherView.as_view(), name='task-dispatcher'),
    
    # Task info endpoint - lists all available tasks
    path('', TasksInfoView.as_view(), name='task-info'),
    
    # Diagnostic endpoint for WebSockets
    path('websocket-diagnostics/', websocket_diagnostics, name='websocket-diagnostics'),
    
    # Legacy URL for backward compatibility
    # path('random-number/', RandomNumberTaskView.as_view(), name='random-number'),
]
