# serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            username=validated_data['email'],  # Use email as username
            password=validated_data['password']
        )
        return user

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class UserTransectionsSerializer(serializers.ModelSerializer):
    plan = PlanSerializer()
    class Meta:
        model = UserTransections
        fields = '__all__'


class UserActivePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivePlan
        fields = '__all__'


class UserActivePlanDataSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    plan = PlanSerializer()
    class Meta:
        model = UserActivePlan
        fields = '__all__'