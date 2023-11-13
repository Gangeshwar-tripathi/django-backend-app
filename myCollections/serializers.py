import re

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from prompt_toolkit.validation import ValidationError
from rest_framework import serializers
from .models import Collections, UserProfile


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collections
        fields = ["title", "description", "movies"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

    @staticmethod
    def validate_email(value):

        email_regex = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid email format.")
        return value

    @staticmethod
    def validate_password(value):
        # Use Django's built-in password validation
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = User.objects.create_user(**validated_data)
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        return user
