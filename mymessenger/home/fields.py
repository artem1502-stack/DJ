from rest_framework import serializers
from .models import OurUser


class OurUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = OurUser.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
        )
        return user

    class Meta:
        model = OurUser
        fields = ("id", "username", "password",)
        # fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].error_messages["required"] = u"username is required"
        self.fields["username"].error_messages["blank"] = u"username cannot be blank"
        # self.fields["email"].error_messages["required"] = u"email is required"
        # self.fields["email"].error_messages["blank"] = u"email cannot be blank"
        self.fields["password"].error_messages[
            "min_length"
        ] = u"password must be at least 8 chars"
