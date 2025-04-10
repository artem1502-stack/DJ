from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from .models import Chat
from django.forms.utils import ErrorList

class ChatForm(forms.ModelForm):
    DIALOG = 'D'
    CHAT = 'C'
    CHAT_TYPE_CHOICES = (
        (DIALOG, 'Dialog'),
        (CHAT, 'Chat'))

    type = models.CharField(
        'Тип',
        max_length=1,
        choices=CHAT_TYPE_CHOICES,
        default=DIALOG
        )

    name = models.CharField('name', max_length=80)
    members = models.ManyToManyField(User, verbose_name="member")
    # chat_id = models.AutoField(unique=True, primary_key=True)

    def clean(self):
        c_d = super().clean()

        c_type = c_d.get("type")
        c_members = c_d.get("members")

        if c_type == "D" and len(c_members) > 2:
            errors = self._errors.setdefault(forms.forms.NON_FIELD_ERRORS, forms.utils.ErrorList())
            errors.append("My error here")
            # raise forms.ValidationError(
            #     "Select only 1 other member for dialog"
            # )
        # if c_type == "D" and not c_name:
        #     raise forms.ValidationError(
        #         "No name for dialog"
        #     )

    class Meta:
        model = Chat
        fields = ("type", "members", "name")


class MessageForm(forms.Form):
    text = forms.CharField()
    date_field = forms.DateField(widget=forms.SelectDateWidget)
    time_field = forms.TimeField(widget=forms.TimeInput)
    boolean_field = forms.BooleanField(required=False)


class ProfileForm(forms.ModelForm):
    # newa_password = forms.CharField(widget=forms.PasswordInput, label="Insert туц password")
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "First name (username by defaul)",
            "last_name": "Last name (optional)",
            "email": "Email (optional)",}


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

