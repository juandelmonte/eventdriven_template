from django.urls import path
from .views import RegisterView, AsyncTokenObtainPairView, AsyncTokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', AsyncTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', AsyncTokenRefreshView.as_view(), name='token_refresh'),
]
