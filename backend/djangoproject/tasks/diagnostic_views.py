from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def websocket_diagnostics(request):
    """Check if WebSocket server is properly set up"""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
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
                "channel_layer_type": channel_layer.__class__.__name__,
            }
        }, status=500)
