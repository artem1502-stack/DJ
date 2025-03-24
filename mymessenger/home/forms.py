from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Message


class ChatForm(forms.ModelForm):
    ...


class MessageForm(forms.Form):
    text = forms.CharField()
    date_field = forms.DateField(widget=forms.SelectDateWidget)
    time_field = forms.TimeField(widget=forms.TimeInput)
    boolean_field = forms.BooleanField(required=False)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    check_password = forms.CharField(widget=forms.PasswordInput, label="Insert password again")

    def clean_check_password(self):
        c_d = self.cleaned_data
        if c_d["password"] != c_d["check_password"]:
            raise forms.ValidationError("Input passwords seem to be different")
        return c_d["check_password"]

    class Meta:
        model = User
        fields = ("username", "email")


class UserLogInForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput, label="Insert your password")

    class Meta:
        model = User
        fields = ("username", "password")


# class UserLogoutForm(AuthenticationForm):
#     username = forms.CharField()
#     password = forms.CharField(widget=forms.PasswordInput, label="Insert your password")
#
#     class Meta:
#         model = User
#         fields = ("username", "password")

