from channels.middleware import BaseMiddleware
from django.db import close_old_connections
from django.conf import settings
from jwt import decode as jwt_decode
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from urllib.parse import parse_qs
import logging
import traceback
import sys
import json

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage after connection is closed
        close_old_connections()
        
        # Only process WebSocket connections
        if scope["type"] != "websocket":
            return await super().__call__(scope, receive, send)
            
        logger.info("============== JWT AUTH MIDDLEWARE ==============")
        logger.info(f"Processing WebSocket connection from {scope.get('client', ['unknown', 0])}")
        
        # Get query parameters
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        logger.info(f"Query string: '{query_string}'")
        logger.info(f"Parsed query params: {query_params}")
        
        # Get token from query parameters
        token = query_params.get('token', [None])[0]
        
        if token:
            logger.info(f"Found token (first 15 chars): {token[:15]}...")
        else:
            logger.warning("No token found in WebSocket connection")
        
        try:
            if token:
                # Decode token
                logger.info("Attempting to decode JWT token...")
                decoded_token = jwt_decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"]
                )
                
                # Store user_id in scope
                scope['user_id'] = decoded_token.get('user_id')
                logger.info(f"Successfully authenticated user_id: {scope['user_id']}")
                
                # Print full decoded token for debugging
                logger.info(f"Decoded token: {json.dumps(decoded_token)}")
            else:
                logger.warning("No token provided, setting user_id to None")
                scope['user_id'] = None
                
        except ExpiredSignatureError:
            logger.error("Token expired")
            scope['user_id'] = None
        except InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            scope['user_id'] = None
        except Exception as e:
            logger.error(f"Unexpected error decoding token: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            scope['user_id'] = None
            
        logger.info("============== END JWT AUTH MIDDLEWARE ==============")
        
        return await super().__call__(scope, receive, send)