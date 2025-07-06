import json
import asyncio
import traceback
import sys
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from redis.asyncio import Redis
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("==========================")
        print("CONSUMER CONNECT CALLED!")
        print("==========================")
        logger.info("CONSUMER CONNECT CALLED!")
        # Temporary fix for testing - accept all connections
        await self.accept()
        self.user_id = "test_user"
        self.group_name = f"user_{self.user_id}"
        
        # Send confirmation
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Connected for testing"
        }))
        
        # Add to group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

    async def connect_old(self):
        logger.info("============== TASK CONSUMER CONNECT ==============")
        
        try:
            # Get user_id from scope
            self.user_id = self.scope.get('user_id')
            logger.info(f"User ID from scope: {self.user_id}")
            
            # DEBUG: Print all available scope data
            safe_scope = {k: v for k, v in self.scope.items() 
                         if k not in ('headers', 'server', 'client')}
            logger.info(f"WebSocket scope: {safe_scope}")
            
            # Accept connection for debugging even if authentication fails
            if settings.DEBUG:
                logger.info("DEBUG mode enabled, accepting connection regardless of authentication")
                await self.accept()
                
                if not self.user_id:
                    logger.warning("No authenticated user but accepting in DEBUG mode")
                    await self.send(text_data=json.dumps({
                        "type": "warning",
                        "message": "Authentication failed but connection accepted in DEBUG mode"
                    }))
                    # Still set a group name for testing
                    self.group_name = "anonymous"
                    self.user_id = "anonymous"
                else:
                    # Create user-specific group name
                    self.group_name = f"user_{self.user_id}"
                    logger.info(f"Using group name: {self.group_name}")
                    
                    await self.send(text_data=json.dumps({
                        "type": "connection_established",
                        "message": f"Connected as user {self.user_id}"
                    }))
            else:
                # Production mode - strict authentication
                if not self.user_id:
                    logger.error("Authentication failed, rejecting WebSocket connection")
                    await self.close(code=4001)
                    return
                
                # Accept the connection
                await self.accept()
                
                # Create user-specific group name
                self.group_name = f"user_{self.user_id}"
                logger.info(f"Using group name: {self.group_name}")
                
                # Send confirmation message
                await self.send(text_data=json.dumps({
                    "type": "connection_established",
                    "message": f"Connected as user {self.user_id}"
                }))
            
            # Add to group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            logger.info(f"Added to channel group: {self.group_name}")
            
            # Send a test message to the group to verify channel layer works
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.message",
                    "message": "Channel layer test message"
                }
            )
            logger.info("Sent test message to channel group")
            
            # CRITICAL PART: Create Redis connection and subscribe to results
            try:
                logger.info("Creating Redis connection...")
                self.redis = Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    decode_responses=True
                )
                logger.info(f"Redis connection established to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
                
                # Subscribe to Redis channel
                self.pubsub = await self.redis.pubsub()
                await self.pubsub.subscribe(settings.REDIS_RESULTS_QUEUE)
                logger.info(f"Subscribed to Redis results queue: {settings.REDIS_RESULTS_QUEUE}")
                
                # Start listening for messages in a background task
                self.listen_task = asyncio.create_task(self.listen_to_redis())
                logger.info("Started Redis listener task")
            except Exception as e:
                logger.error(f"Error setting up Redis connection: {str(e)}")
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Redis connection error: {str(e)}"
                }))
            
            logger.info("============== END TASK CONSUMER CONNECT ==============")
            
        except Exception as e:
            logger.error(f"Exception in connect: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            if not hasattr(self, 'accepted') or not self.accepted:
                await self.close(code=4500)
            else:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Error: {str(e)}"
                }))
    
    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnect called with code: {close_code}")
        
        # Clean up Redis resources
        if hasattr(self, 'listen_task'):
            logger.info("Cancelling Redis listener task")
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass
            
        if hasattr(self, 'pubsub'):
            logger.info("Unsubscribing from Redis")
            await self.pubsub.unsubscribe()
            
        if hasattr(self, 'redis'):
            logger.info("Closing Redis connection")
            await self.redis.close()
        
        # Clean up channel resources
        if hasattr(self, 'group_name') and hasattr(self, 'channel_name'):
            try:
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
                logger.info(f"Removed from channel group: {self.group_name}")
            except Exception as e:
                logger.error(f"Error removing from group: {str(e)}")
    
    async def listen_to_redis(self):
        """
        Listen for messages on the Redis results queue and forward them to the WebSocket.
        This connects Celery task results to the WebSocket client.
        """
        logger.info(f"Redis listener started for user {self.user_id}")
        try:
            while True:
                try:
                    message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                    if message and message['type'] == 'message':
                        logger.debug(f"Received message from Redis: {message['data']}")
                        
                        try:
                            # Parse the JSON data
                            data = json.loads(message['data'])
                            
                            # Check if this message is for the current user
                            message_user_id = data.get('user_id')
                            if message_user_id is not None and str(message_user_id) == str(self.user_id):
                                logger.info(f"Forwarding task result to user {self.user_id}")
                                
                                # Option 1: Send directly to the WebSocket
                                await self.send(text_data=json.dumps(data))
                                
                                # Option 2: Send via channel layer (if you want to broadcast to multiple sessions)
                                # await self.channel_layer.group_send(
                                #     self.group_name,
                                #     {
                                #         "type": "task.result",
                                #         "data": data
                                #     }
                                # )
                            else:
                                logger.debug(f"Ignoring message for user {message_user_id} (current: {self.user_id})")
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON from Redis: {message['data']}")
                        except Exception as e:
                            logger.error(f"Error processing Redis message: {str(e)}")
                            traceback.print_exc(file=sys.stderr)
                
                except asyncio.CancelledError:
                    logger.info("Redis listener cancelled")
                    raise
                except Exception as e:
                    logger.error(f"Error in Redis listener loop: {str(e)}")
                    traceback.print_exc(file=sys.stderr)
                
                # Small delay to prevent CPU hogging
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("Redis listener task cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error in Redis listener: {str(e)}")
            traceback.print_exc(file=sys.stderr)
    
    async def receive(self, text_data):
        logger.info(f"Received message from WebSocket: {text_data}")
        
        try:
            # Echo back for testing
            await self.send(text_data=json.dumps({
                "type": "echo",
                "message": text_data
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
    
    async def chat_message(self, event):
        """Handle messages sent to the group"""
        logger.info(f"Received group message: {event}")
        
        try:
            message = event["message"]
            await self.send(text_data=json.dumps({
                "type": "chat.message",
                "message": message
            }))
        except Exception as e:
            logger.error(f"Error in chat_message: {str(e)}")
    
    async def task_result(self, event):
        """Handle task result messages from the channel layer"""
        logger.info(f"Received task result via channel layer: {event}")
        
        try:
            await self.send(text_data=json.dumps(event["data"]))
        except Exception as e:
            logger.error(f"Error in task_result: {str(e)}")