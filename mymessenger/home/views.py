from django.contrib.auth.models import User, Permission
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.decorators import login_required, permission_required
from django.views import View
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone
from django.forms import modelformset_factory
from .models import Message, Chat
from .forms import MessageForm, UserRegistrationForm, UserLoginForm, ChatForm, DialogForm, ProfileForm
import datetime


def get_messages2():
    messages = Message.objects.all()
    return messages


def get_chats(user):
    chats = Chat.objects.filter(members=user)

    chat_data = []
    for chat in chats:

        cur_members = (chat.members.all())
        if chat.type == "D":
            name = str(chat.members.all()[0])
        else:
            name = chat.name

        cur_chat = f"{chat.id}) Name: {name} ({chat.type}) \ \ \n Users: {list(map(str, cur_members))}"
        chat_data.append(cur_chat)

    return chat_data


class SaveInputMessage(View):
    def post(self, request):
        form = MessageForm(request.POST)
        if form.is_valid():
            text = request.POST.get("text")

            def convert_date():
                date_field_day = int(request.POST.get("date_field_day"))
                date_field_month = int(request.POST.get("date_field_month"))
                date_field_year = int(request.POST.get("date_field_year"))

                time_field = request.POST.get("time_field").split(":")
                time_hours_field = int(time_field[0])
                time_minutes_field = int(time_field[1])
                if len(time_field) == 3:
                    time_seconds_field = int(time_field[2])
                else:
                    time_seconds_field = 0

                date_time = datetime.datetime(year=date_field_year,
                                              month=date_field_month,
                                              day=date_field_day,
                                              hour=time_hours_field,
                                              minute=time_minutes_field,
                                              second=time_seconds_field)
                return date_time

            date_time = convert_date()
            boolean_field = bool(request.POST.get("boolean_field"))

            message = Message(content=text, pud_date=date_time, is_read=boolean_field)
            message.save()


@method_decorator(login_required, name="dispatch")
class Index(View):
    def get(self, request):
        chats = Chat.objects.filter(members=request.user)

        return render(request, 'home/index.html', {
            'chats': chats,
            'user': request.user
        })


def registration(requests):
    if requests.method == "POST":
        user_form = UserRegistrationForm(requests.POST)

        if user_form.is_valid():
            new_user = user_form.save()
            new_user.set_password(user_form.cleaned_data["password"])
            # permissions = [("can_change_user", "Can change user"),  ("can_view_user", "Can view user"),
            # ("can_add_chat", "Can add chat"), ("can_view_chat", "Can change chat"),
            # ("can_add_message", "Can add message"), ("can_view_message", "Can change message"),
            # ]
            permission = Permission.objects.all()
            new_user.user_permissions.set(permission)

            new_user.save()
    user_registration_form = UserRegistrationForm()
    users = User.objects.all()
    return render(requests, "registration/registration.html", {'user_registration_form': user_registration_form,
                                                               'users': users})


class CreateChatOrDialog(View):
    def post(self, request, form_template):
        if "type_chosen" in request.POST:
            chat_form = form_template(request.POST, request.FILES, user=request.user)
            if chat_form.is_valid():
                new_chat = chat_form.save()  # then add current user to queryset (members) probably through cleaned_data
                new_chat.members.add(request.user)
                new_chat.save()
                return redirect(new_chat)
        else:
            chat_form = form_template(user=request.user)
        return render(request, "chat/create_chat.html", {
            'chat_form': chat_form, 'user': request.user
        })


class CreateChat(View):

    def get_post(self, request):
        c_or_d = CreateChatOrDialog()
        return c_or_d.post(request=request, form_template=ChatForm)

    def get(self, request):
        return self.get_post(request)

    def post(self, request):
        return self.get_post(request)


def create_dialog(request):
    c_or_d = CreateChatOrDialog()
    return c_or_d.post(request=request, form_template=DialogForm)


def get_messages_in_chat(chat_id):
    try:
        messages = Message.objects.filter(chat_id=chat_id)
    except Message.DoesNotExist:
        messages = "Your chat is empty :("
    return messages


@login_required(login_url="/login")
@permission_required("home.view_chat", raise_exception=True)
def chat(requests, id):
    try:
        cur_chat = Chat.objects.get(id=id)
        if requests.user not in cur_chat.members.all():
            raise PermissionDenied("Permission Denied")
        if requests.method == "POST" and "send_message" in requests.POST:
            try:
                text = requests.POST.get("text")
                message = Message(content=text, pud_date=timezone.now(), is_read=False, sender=requests.user,
                                  chat=cur_chat)
                message.save()
            except Message.DoesNotExist:
                ...
        chat_messages = get_messages_in_chat(id)
        for chat_message in chat_messages:
            if chat_message.sender != requests.user and not chat_message.is_read:
                chat_message.is_read = True
                chat_message.save()
        message_form = MessageForm()
        return render(requests, "chat/chat.html",
                      {'chat': cur_chat, 'chat_messages': chat_messages,
                       'user': requests.user, 'message_form': message_form})
    except Chat.DoesNotExist:
        return HttpResponse("Chat not found")
    except PermissionDenied:
        return redirect("/")


def get_profile_data(username):
    data = User.objects.get(username=username)
    return data


@method_decorator(login_required, name="dispatch")
@method_decorator(permission_required("auth.change_user", raise_exception=True), name="dispatch")
class UserProfile(View):

    def get(self, request, username):
        try:
            profile_data = get_profile_data(username)

            try:
                profile_form = ProfileForm(initial={
                    "first_name": profile_data.first_name,
                    "last_name": profile_data.last_name,
                    "email": profile_data.email
                })
                if str(request.user) != username:
                    raise PermissionDenied("Permission Denied")

                return render(request, "user/own_profile.html", {
                    "data": request.user,
                    "profile_form": profile_form,
                    "user_changed": False})

            except PermissionDenied:
                return render(request, "user/other_profile.html", {"user": request.user, "data": profile_data})
        except User.DoesNotExist:
            return HttpResponse("User not found")

    def post(self, request, username):
        if "change_profile" in request.POST:
            profile_data = get_profile_data(username)
            profile_data.first_name = request.POST['first_name']
            profile_data.last_name = request.POST['last_name']
            profile_data.email = request.POST['email']

            user_changed = True

            profile_data.save()

            profile_form = ProfileForm(request.POST, initial={
                "first_name": profile_data.first_name,
                "last_name": profile_data.last_name,
                "email": profile_data.email
            })

            return render(request, "user/own_profile.html", {
                "data": profile_data,
                "profile_form": profile_form,
                "user_changed": user_changed})


@method_decorator(login_required, name="dispatch")
class ChangePassword(PasswordChangeView):
    template_name = "user/change_password.html"
    username = None

    def get_object(self):
        self.username = str(self.request.user)
        return super().get_object()


@method_decorator(login_required, name="dispatch")
class PasswordChangeDone(View):
    def get(self, request):
        return redirect(reverse_lazy("user_profile", kwargs={"username": request.user}))


class LoginUser(LoginView):
    next_page = '/'
    form_class = UserLoginForm
    template_name = "login/login.html"


class LogoutUser(LogoutView):
    next_page = '/login'
    template_name = "login/login.html"
