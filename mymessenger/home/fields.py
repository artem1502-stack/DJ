from rest_framework import serializers
from .models import OurUser
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token


class OurUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = OurUser
        fields = ("username", "password")


class RegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True )

    class Meta:
        model = OurUser
        fields = ("id", "username", "email", "password", "confirm_password")
        extra_kwargs = {
            'password': {'write_only': True}
        }
        # fields = '__all__'

    def save(self, **kwargs):
        new_user = OurUser(
            username=self.validated_data['username'],
            email=self.validated_data['email']
        )
        password = self.validated_data['password']
        confirm_password = self.validated_data['confirm_password']

        if password != confirm_password:
            raise serializers.ValidationError({'password': 'Passwords did not match'})

        new_user.set_password(password)
        new_user.save()
        return new_user
