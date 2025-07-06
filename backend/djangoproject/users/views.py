from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
from .serializers import UserSerializer

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer

@method_decorator(csrf_exempt, name='dispatch')
class AsyncTokenObtainPairView(TokenObtainPairView):
    """
    Token view that works with both regular HTTP and WebSockets.
    """
    # Just use the default implementation
    pass

@method_decorator(csrf_exempt, name='dispatch')
class AsyncTokenRefreshView(TokenRefreshView):
    """
    Token refresh view that works with both regular HTTP and WebSockets.
    """
    # Just use the default implementation
    pass
