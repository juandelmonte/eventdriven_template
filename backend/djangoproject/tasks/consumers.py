from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from redis.asyncio import Redis
import json
import asyncio
import logging
import traceback
import sys

logger = logging.getLogger(__name__)

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Get user_id from scope (set by middleware)
            user_id = self.scope.get('user_id')
            
            logger.info(f"WebSocket connect attempt with scope: {self.scope}")
            
            if not user_id:
                logger.warning("No authenticated user found, closing connection")
                await self.close(code=4001)
                return
                
            # Store user_id for later use
            self.user_id = user_id
            logger.info(f"User authenticated with ID: {user_id}")
            
            # Create user-specific group name
            self.group_name = f"user_{self.user_id}"
            
            # Accept the connection FIRST before any other async operations
            await self.accept()
            logger.info(f"WebSocket connection accepted for user {self.user_id}")
            
            # Send initial confirmation message
            await self.send(text_data=json.dumps({
                "type": "connection_established",
                "message": f"Connected as user {self.user_id}"
            }))
            
            # Then add to group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            logger.info(f"Added to channel group: {self.group_name}")
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            await self.close(code=4500)
            return
        
        # Create Redis connection
        try:
            logger.info("Creating Redis connection...")
            self.redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
            
            # Subscribe to Redis channel
            logger.info("Creating Redis PubSub...")
            self.pubsub = await self.redis.pubsub()
            await self.pubsub.subscribe(settings.REDIS_RESULTS_QUEUE)
            logger.info(f"Subscribed to Redis channel: {settings.REDIS_RESULTS_QUEUE}")
            
            # Start listening for messages
            logger.info("Starting Redis listener task...")
            self.listen_task = asyncio.create_task(self.listen_to_redis())
            logger.info("Redis listener task started")
        except Exception as e:
            logger.error(f"Error setting up Redis: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            await self.close(code=4002)

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnect called with code: {close_code}")
        
        try:
            # Cancel background task
            if hasattr(self, 'listen_task'):
                logger.info("Cancelling Redis listener task")
                self.listen_task.cancel()
                try:
                    await self.listen_task
                except asyncio.CancelledError:
                    pass
                logger.info("Redis listener task cancelled")
            
            # Clean up Redis connection
            if hasattr(self, 'pubsub'):
                logger.info("Unsubscribing from Redis")
                await self.pubsub.unsubscribe()
                logger.info("Unsubscribed from Redis")
                
            if hasattr(self, 'redis'):
                logger.info("Closing Redis connection")
                await self.redis.close()
                logger.info("Redis connection closed")
            
            # Remove from channel group
            if hasattr(self, 'group_name') and hasattr(self, 'channel_name'):
                logger.info(f"Removing from group: {self.group_name}")
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
                logger.info("Removed from group")
                
        except Exception as e:
            logger.error(f"ERROR in disconnect: {str(e)}")
            traceback.print_exc(file=sys.stdout)

    async def listen_to_redis(self):
        """Listen for messages from Redis and forward to WebSocket"""
        logger.info(f"Redis listener started for user {self.user_id}")
        try:
            while True:
                try:
                    message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                    if message and message['type'] == 'message':
                        logger.debug(f"Received message from Redis: {message['data']}")
                        
                        try:
                            data = json.loads(message['data'])
                            logger.debug(f"Message JSON data: {data}")
                            
                            # Check if this message is for the current user
                            if str(data.get('user_id')) == str(self.user_id):
                                logger.info(f"Message is for user {self.user_id}, sending to WebSocket")
                                await self.send(text_data=json.dumps(data))
                                logger.info("Message sent to WebSocket")
                                
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON from Redis: {message['data']}")
                        except Exception as e:
                            logger.error(f"Error processing Redis message: {str(e)}")
                            traceback.print_exc(file=sys.stdout)
                            
                except Exception as e:
                    logger.error(f"Error in Redis message loop: {str(e)}")
                    traceback.print_exc(file=sys.stdout)
                
                # Small delay to prevent CPU hogging
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("Redis listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Redis listener: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            await self.close(code=1011)
            
    async def task_update(self, event):
        """Handle task updates and send to WebSocket"""
        try:
            logger.info(f"Sending task update to user {self.user_id}")
            await self.send(text_data=json.dumps(event['message']))
            logger.info("Task update sent")
        except Exception as e:
            logger.error(f"Error sending task update: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            logger.debug(f"Received WebSocket message: {text_data}")
            # Echo back message for testing
            await self.send(text_data=json.dumps({
                'type': 'echo',
                'message': text_data
            }))
            logger.debug("Sent echo response")
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            traceback.print_exc(file=sys.stdout)