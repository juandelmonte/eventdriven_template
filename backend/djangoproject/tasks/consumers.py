import json
import asyncio
import aioredis
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class TaskConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for task updates.
    
    This consumer:
    1. Authenticates users via WebSocket
    2. Listens to Redis for task results
    3. Forwards results to the appropriate user via WebSocket
    """
    
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            self.user_id = user.id
            self.user_group = f"user_{self.user_id}"
            
            # Add to user's group
            await self.channel_layer.group_add(
                self.user_group,
                self.channel_name
            )
            await self.accept()
            
            # Start Redis listener task
            asyncio.create_task(self.listen_to_redis())
    
    async def disconnect(self, close_code):
        # Remove from user's group
        await self.channel_layer.group_discard(
            self.user_group,
            self.channel_name
        )
    
    async def task_update(self, event):
        """Send task update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'task_update',
            'task': event['task']
        }))
    
    async def listen_to_redis(self):
        """Listen to Redis for task results"""
        redis = await aioredis.create_redis_pool(
            f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
        )
        
        # Subscribe to results channel
        channel = (await redis.subscribe(settings.REDIS_RESULTS_QUEUE))[0]
        
        try:
            while True:
                # Wait for a message
                message = await channel.get()
                if message:
                    data = json.loads(message)
                    
                    # Check if this message is for this user
                    if str(data.get('user_id')) == str(self.user_id):
                        # Send to user's group
                        await self.channel_layer.group_send(
                            self.user_group,
                            {
                                'type': 'task_update',
                                'task': {
                                    'task_id': data.get('task_id'),
                                    'task_type': data.get('task_type'),
                                    'status': data.get('status'),
                                    'result': data.get('result')
                                }
                            }
                        )
        except asyncio.CancelledError:
            # Unsubscribe when cancelled
            redis.unsubscribe(settings.REDIS_RESULTS_QUEUE)
            redis.close()
            await redis.wait_closed()
