from django.http import HttpResponse
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from .models import Chat


class ChatForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['members'].queryset = User.objects.exclude(username=user)
        self.user = user

    class Meta:
        model = Chat
        fields = ("name", "members")

    def clean_members(self):
        c_d = self.cleaned_data
        if self.user not in c_d["members"]:
            # self.data = self.data.copy()
            # self.data['members'] += str(self.user)
            self.fields['members'].queryset |= User.objects.filter(username=self.user)
        return c_d["members"]


class DialogForm(forms.Form):  # prev: forms.ModelForm // BaseModelFormSet

    #  in order to use ModelChoiceField, the original field in the model has to have be ForeignKey, NOT ManyToMany
    members = forms.ModelChoiceField(
        queryset=(User.objects.all()),
        empty_label="Choose a user",
        widget=forms.Select,
        required=True
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['members'] = forms.ModelChoiceField(widget=forms.Select, empty_label="Choose a user",
                                                                queryset=User.objects.all())

        if user is not None:
            self.fields['members'].queryset = User.objects.exclude(username=user)

    # def clean_type(self):
    #     ...

    class Meta:
        model = Chat
        fields = ("members",)


class MessageForm(forms.Form):
    text = forms.CharField()
    date_field = forms.DateField(widget=forms.SelectDateWidget)
    time_field = forms.TimeField(widget=forms.TimeInput)
    boolean_field = forms.BooleanField(required=False)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "First name (username by default)",
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


class UserLoginForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput, label="Insert your password")

    class Meta:
        model = User
        fields = ("username", "password")
