from rest_framework import serializers
from .models import OurUser


class RegistrationSerializer(serializers.ModelSerializer):
    """
    A serializer, used to registrate new users.
    """
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = OurUser
        fields = ("id", "username", "email", "password", "confirm_password")
        # Making password the password only .
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def save(self, **kwargs):
        """
        Performs validation and (if valid) creates a new user.
        """
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
