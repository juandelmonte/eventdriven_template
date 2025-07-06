from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register User model with the admin site using Django's UserAdmin
admin.site.register(User, UserAdmin)
