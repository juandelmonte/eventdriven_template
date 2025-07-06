from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
import traceback
import sys
import json

logger = logging.getLogger(__name__)

@csrf_exempt
def websocket_diagnostics(request):
    """Check if WebSocket server is properly set up"""
    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            "diagnostics",
            {
                "type": "echo.message",
                "message": "Diagnostic test",
            },
        )
        return JsonResponse({
            "status": "success",
            "message": "Channel layer is working properly",
            "setup": {
                "channel_layer_type": channel_layer.__class__.__name__,
                "backend": getattr(channel_layer, "connection_settings", {}).get("backend", "unknown"),
                "hosts": getattr(channel_layer, "connection_settings", {}).get("hosts", []),
            }
        })
    except Exception as e:
        logger.exception("Error in WebSocket diagnostics")
        return JsonResponse({
            "status": "error",
            "message": str(e),
            "setup": {
                "channel_layer_type": channel_layer.__class__.__name__ if channel_layer else "None",
            }
        }, status=500)

@csrf_exempt
def test_channel_layer(request):
    """
    Test the channel layer by sending a message to a specific user group
    """
    try:
        user_id = request.GET.get('user_id', '1')  # Default to user 1 if not specified
        message = request.GET.get('message', 'Test message')
        
        # Get channel layer
        channel_layer = get_channel_layer()
        if not channel_layer:
            return JsonResponse({'status': 'error', 'message': 'Could not get channel layer'}, status=500)
        
        # Create a group name
        group_name = f"user_{user_id}"
        
        # Log the attempt
        logger.info(f"Attempting to send message to group: {group_name}")
        
        # Send to the group
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'task_update',
                'message': {
                    'type': 'diagnostic',
                    'content': message,
                    'user_id': user_id
                }
            }
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Message sent to group {group_name}',
            'details': {
                'group': group_name,
                'message_content': message
            }
        })
        
    except Exception as e:
        logger.error(f"Error in test_channel_layer: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
