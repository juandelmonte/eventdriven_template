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
            logger.info("Sent test message to channel group")                # CRITICAL PART: Create Redis connection and subscribe to results
            try:
                logger.info("Creating Redis connection...")
                logger.info(f"Redis settings: host={settings.REDIS_HOST}, port={settings.REDIS_PORT}")
                logger.info(f"Redis results queue: {settings.REDIS_RESULTS_QUEUE}")
                
                # Send info to client
                await self.send(text_data=json.dumps({
                    "type": "info",
                    "message": f"Connecting to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}"
                }))
                
                self.redis = Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    decode_responses=True
                )
                logger.info(f"Redis connection established to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
                
                # Send confirmation to client
                await self.send(text_data=json.dumps({
                    "type": "info",
                    "message": "Redis connection established"
                }))
                
                # Test Redis connection first
                redis_test = await self.test_redis_connection()
                if redis_test:
                    logger.info("Redis connection test passed")
                    await self.send(text_data=json.dumps({
                        "type": "info",
                        "message": "Redis connection test successful"
                    }))
                else:
                    logger.warning("Redis connection test failed")
                    await self.send(text_data=json.dumps({
                        "type": "warning",
                        "message": "Redis connection test failed"
                    }))
                
                # Create PubSub instance
                self.pubsub = self.redis.pubsub()
                logger.info("Created Redis PubSub instance")
                
                # Subscribe to Redis channel - this method IS awaitable
                await self.pubsub.subscribe(settings.REDIS_RESULTS_QUEUE)
                logger.info(f"Subscribed to Redis results queue: {settings.REDIS_RESULTS_QUEUE}")
                
                # Start listening for messages in a background task
                self.listen_task = asyncio.create_task(self.listen_to_redis())
                logger.info("Started Redis listener task")
            except Exception as e:
                logger.error(f"Error setting up Redis connection: {str(e)}")
                traceback.print_exc(file=sys.stderr)
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
        logger.info(f"Listening on queue: {settings.REDIS_RESULTS_QUEUE}")
        
        # Set up the pubsub if not already done
        if not hasattr(self, 'pubsub') or self.pubsub is None:
            logger.warning("PubSub not initialized, creating new one")
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(settings.REDIS_RESULTS_QUEUE)
            
        # Send confirmation to the client
        await self.send(text_data=json.dumps({
            "type": "info",
            "message": f"Subscribed to Redis queue: {settings.REDIS_RESULTS_QUEUE}"
        }))
        
        msg_count = 0
        heartbeat_count = 0
        
        try:
            while True:
                try:
                    # Increment heartbeat counter
                    heartbeat_count += 1
                    
                    # Every 100 iterations, send a heartbeat message to confirm the connection is active
                    if heartbeat_count >= 100:  # Every ~10 seconds
                        heartbeat_count = 0
                        logger.info(f"Redis listener heartbeat for user {self.user_id}")
                        await self.send(text_data=json.dumps({
                            "type": "heartbeat",
                            "message": "Redis listener still active"
                        }))
                    
                    # get_message is awaitable in the async Redis client
                    message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                    
                    if message:
                        msg_count += 1
                        logger.info(f"Redis message received #{msg_count}: {message}")
                        
                        # Inform client about message type for debugging
                        await self.send(text_data=json.dumps({
                            "type": "debug",
                            "message": f"Received Redis message type: {message['type']}"
                        }))
                        
                        if message['type'] == 'message':
                            data = message['data']
                            logger.info(f"Message data: {data}")
                            
                            try:
                                # Parse the JSON data
                                parsed_data = json.loads(data)
                                logger.info(f"Parsed message data: {parsed_data}")
                                
                                # Check if this message is for the current user
                                message_user_id = parsed_data.get('user_id')
                                logger.info(f"Message user_id: {message_user_id}, current user_id: {self.user_id}")
                                
                                # For debugging, send info about the message
                                await self.send(text_data=json.dumps({
                                    "type": "debug",
                                    "message": f"Message for user: {message_user_id}, current user: {self.user_id}"
                                }))
                                
                                # If the message is for this user or no user is specified, forward it
                                if message_user_id is not None and str(message_user_id) == str(self.user_id):
                                    logger.info(f"Forwarding message to user {self.user_id}")
                                    
                                    # Format the message as a task result
                                    result_message = {
                                        "type": "task_result",
                                        "data": parsed_data
                                    }
                                    
                                    # Send to WebSocket
                                    await self.send(text_data=json.dumps(result_message))
                                    
                                    # Log success
                                    logger.info(f"Message forwarded to user {self.user_id}")
                                else:
                                    logger.info(f"Ignoring message for user {message_user_id} (not for current user {self.user_id})")
                            except json.JSONDecodeError:
                                logger.error(f"Failed to decode JSON from Redis: {data}")
                                await self.send(text_data=json.dumps({
                                    "type": "error",
                                    "message": f"Failed to decode Redis message: {data[:100]}"
                                }))
                            except Exception as e:
                                logger.error(f"Error processing Redis message: {str(e)}")
                                traceback.print_exc(file=sys.stderr)
                                await self.send(text_data=json.dumps({
                                    "type": "error",
                                    "message": f"Error processing Redis message: {str(e)}"
                                }))
                    
                except asyncio.CancelledError:
                    logger.info("Redis listener cancelled")
                    raise
                except Exception as e:
                    logger.error(f"Error in Redis listener loop: {str(e)}")
                    traceback.print_exc(file=sys.stderr)
                    
                    # Inform client about the error
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": f"Redis listener error: {str(e)}"
                    }))
                    
                    # Pause briefly before continuing
                    await asyncio.sleep(1)
                    
                # Small delay to prevent CPU hogging
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info(f"Redis listener task cancelled for user {self.user_id}")
            raise
        except Exception as e:
            logger.error(f"Fatal error in Redis listener: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            
            # Try to inform the client
            try:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Redis listener fatal error: {str(e)}"
                }))
            except:
                pass

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
    
    async def test_redis_connection(self):
        """Test if Redis connection is working properly"""
        try:
            # Log Redis configuration
            logger.info(f"Testing Redis connection to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            logger.info(f"Results queue: {settings.REDIS_RESULTS_QUEUE}")
            
            # Test basic operations
            test_key = f"test_key_{self.user_id}"
            test_value = f"test_value_{self.user_id}"
            
            # Set a value
            await self.redis.set(test_key, test_value)
            logger.info(f"Set Redis test key: {test_key}")
            
            # Get the value
            result = await self.redis.get(test_key)
            logger.info(f"Got Redis test value: {result}")
            
            if result != test_value:
                logger.error(f"Redis test value mismatch: expected {test_value}, got {result}")
                await self.send(text_data=json.dumps({
                    "type": "warning",
                    "message": "Redis GET/SET test failed: values don't match"
                }))
                return False
                
            # Clean up
            await self.redis.delete(test_key)
            logger.info(f"Deleted Redis test key: {test_key}")
            
            # Test pub/sub manually on the main queue
            test_message = {
                "user_id": self.user_id,
                "task_id": "connection-test",
                "task_type": "test",
                "status": "test",
                "result": {"message": "Connection test"}
            }
            
            # Publish a message to the results queue
            json_message = json.dumps(test_message)
            pub_result = await self.redis.publish(settings.REDIS_RESULTS_QUEUE, json_message)
            logger.info(f"Published test message to {settings.REDIS_RESULTS_QUEUE}, result: {pub_result}")
            
            # Send confirmation to client
            await self.send(text_data=json.dumps({
                "type": "info",
                "message": f"Redis connection test successful. Published test message with result: {pub_result}"
            }))
            
            return True
        except Exception as e:
            error_msg = f"Redis test failed: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc(file=sys.stderr)
            
            # Send error to client
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": error_msg
            }))
            
            return False