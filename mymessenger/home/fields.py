from rest_framework import serializers
from .models import OurUser
from django.core.exceptions import ValidationError


class OurUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = OurUser
        fields = ("username", "password")


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = OurUser
        fields = ("id", "username", "password", "email")
        # fields = '__all__'
