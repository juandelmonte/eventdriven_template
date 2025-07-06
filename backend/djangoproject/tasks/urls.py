from django.urls import path
from .views import TaskDispatcherView, TasksInfoView, test_redis_publish
from .diagnostic_views import websocket_diagnostics, test_channel_layer

urlpatterns = [
    # Task info endpoint - lists all available tasks
    path('', TasksInfoView.as_view(), name='task-info'),
    
    # Diagnostic endpoints for WebSockets
    path('diagnostics/', websocket_diagnostics, name='websocket-diagnostics'),
    path('test-channel/', test_channel_layer, name='test-channel'),
    path('test-redis/', test_redis_publish, name='test-redis'),
    
    # Generic task dispatcher - handles all task types
    # Note: This must be last as it's a catch-all pattern
    path('<str:task_type>/', TaskDispatcherView.as_view(), name='task-dispatcher'),
]
