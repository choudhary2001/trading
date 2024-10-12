# analytics/serializers.py
from rest_framework import serializers
from .models import *

class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeAlert
        fields = '__all__'


class StrategyDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyData
        fields = '__all__'

class ApiIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiIntegration
        fields = ['id', 'api_name', 'broker', 'api_key', 'secret_key', 'api_type', 'status', 'created_at']

    def to_representation(self, instance):
        """Customize how sensitive data (api_key, secret_key) is returned."""
        representation = super().to_representation(instance)
        
        # Show only the first 4 characters and mask the rest with '****'
        if instance.api_key:
            representation['api_key'] = instance.api_key[:4] + '****'
        if instance.secret_key:
            representation['secret_key'] = instance.secret_key[:4] + '****'
        
        return representation


class OrderSerializer(serializers.ModelSerializer):
    # api = ApiIntegrationSerializer()
    class Meta:
        model = Orders
        fields = '__all__'


class OrderDataSerializer(serializers.ModelSerializer):
    api = ApiIntegrationSerializer()
    class Meta:
        model = Orders
        fields = '__all__'


class OpenOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenOrders
        fields = "__all__"