from rest_framework import serializers
from .models import OurUser
from django.core.exceptions import ValidationError

class OurUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = OurUser.objects.get_or_create(
            username=validated_data['username'],
            password=validated_data['password'],
        )
        return user

    class Meta:
        model = OurUser
        fields = ("id", "username", "password",)
        # fields = '__all__'

    def is_valid(self, raise_exception=False):
        if self.data["username"] == "" or len(self.data["password"]) < 8:
            if raise_exception:
                raise ValidationError("Wrong username or password")
        else:
            self.validated_data["user"] = OurUser.objects.get(username=self.data["username"])
            self.validated_data["password"] = self.data["password"]


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields["username"].error_messages["required"] = u"username is required"
        #self.fields["username"].error_messages["blank"] = u"username cannot be blank"
        # self.fields["email"].error_messages["required"] = u"email is required"
        # self.fields["email"].error_messages["blank"] = u"email cannot be blank"
        #self.fields["password"].error_messages[
        #    "min_length"
        #] = u"password must be at least 8 chars"
