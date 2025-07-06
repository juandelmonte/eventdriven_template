from channels.middleware import BaseMiddleware
from django.db import close_old_connections
from django.conf import settings
from jwt import decode as jwt_decode
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from urllib.parse import parse_qs
import logging
import traceback
import sys

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage after connection is closed
        close_old_connections()
        
        # Get query parameters
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        logger.info(f"Processing WebSocket connection with query string: {query_string}")
        
        # Get token from query parameters
        token = query_params.get('token', [None])[0]
        logger.info(f"Token found: {bool(token)}")
        
        try:
            if token:
                logger.info("Attempting to decode token")
                # Decode token
                decoded_token = jwt_decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"],
                    options={"verify_signature": True}
                )
                
                # Store user_id in scope - we'll load the actual user object later
                scope['user_id'] = decoded_token.get('user_id')
                logger.info(f"Authentication successful for user_id: {scope['user_id']}")
            else:
                logger.warning("No token found in WebSocket connection")
                scope['user_id'] = None
                
        except ExpiredSignatureError:
            logger.warning("WebSocket authentication failed: Token has expired")
            scope['user_id'] = None
        except InvalidTokenError as e:
            logger.warning(f"WebSocket authentication failed: Invalid token: {str(e)}")
            scope['user_id'] = None
        except Exception as e:
            logger.error(f"Unexpected error processing WebSocket token: {str(e)}")
            traceback.print_exc(file=sys.stdout)
            scope['user_id'] = None
        
        return await super().__call__(scope, receive, send)