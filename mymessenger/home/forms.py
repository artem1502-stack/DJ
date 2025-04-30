from django.http import HttpResponse
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Multichat, Dialog


class ChatForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['members'].queryset = User.objects.exclude(username=user)
        self.user = user

    class Meta:
        model = Multichat
        fields = ("name", "members")

    def clean_members(self):
        c_d = self.cleaned_data
        if self.user not in c_d["members"]:
            self.fields['members'].queryset |= User.objects.filter(username=self.user)
        return c_d["members"]


class DialogForm(forms.ModelForm):
    member1 = forms.ModelChoiceField(
        queryset=(User.objects.all()),
        empty_label="Choose a user",
        widget=forms.Select,
        required=True
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member1'] = forms.ModelChoiceField(widget=forms.Select, empty_label="Choose a user",
                                                                             queryset=User.objects.all())

        if user is not None:
            self.fields['member1'].queryset = User.objects.exclude(username=user)
            # self.fields['member2'].queryset = User.objects.filter(username=user)

    class Meta:
        model = Dialog
        fields = ("member1",)


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
