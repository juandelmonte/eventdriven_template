from rest_framework import serializers

class GenerateRandomNumberSerializer(serializers.Serializer):
    """Serializer for generating random number task request"""
    min_value = serializers.IntegerField(default=1)
    max_value = serializers.IntegerField(default=100)

class ReverseStringSerializer(serializers.Serializer):
    """Serializer for reversing a string task request"""
    text = serializers.CharField(max_length=1000)

class TaskResponseSerializer(serializers.Serializer):
    """Serializer for task responses"""
    task_id = serializers.CharField()
    task_type = serializers.CharField()
    status = serializers.CharField()
    
class TaskResultSerializer(serializers.Serializer):
    """Serializer for task results from WebSocket"""
    task_id = serializers.CharField()
    task_type = serializers.CharField()
    status = serializers.CharField()
    result = serializers.JSONField(required=False)
