from django.contrib.auth.models import Permission
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.decorators import login_required, permission_required
from django.views import View
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from .models import OurUser, Message, Dialog, Chat, DELETED_USER
from .forms import MessageForm, UserRegistrationForm, UserLoginForm, ChatForm, DialogForm, ProfileForm
import datetime


def get_messages2():
    messages = Message.objects.all()
    return messages


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
        chats = Chat.objects.filter(Q(multichat__members=request.user)\
            | Q(dialog__member1=request.user) | Q(dialog__member2=request.user))
        return render(request, 'home/index.html', {
            'chats': chats,
            'user': request.user
        })


def registration(requests):
    message = ''
    if requests.method == "POST":
        user_form = UserRegistrationForm(requests.POST)

        if user_form.is_valid():
            new_user = user_form.save()
            new_user.set_password(user_form.cleaned_data["password"])
            # permissions = [("can_change_user", "Can change user"),  ("can_view_user", "Can view user"),
            # ("can_add_chat", "Can add chat"), ("can_view_chat", "Can change chat"),
            # ("can_add_message", "Can add message"), ("can_view_message", "Can change message"),
            # ]

            permission = Permission.objects.get(
                codename="base_permission"
            )
            new_user.user_permissions.add(permission)

            new_user.save()
            return redirect("/")
        else:
            message = "Username is taken or it contains incorrect characters"
    user_registration_form = UserRegistrationForm()
    users = OurUser.objects.all()
    return render(requests, "registration/registration.html", {'user_registration_form': user_registration_form,
                                                               'users': users, 'message': message})


class CreateChatOrDialog(View):

    def get_form_template(self, request):
        if request.resolver_match.view_name == "create_chat":
            return ChatForm
        return DialogForm

    def post(self, request):
        form_template = self.get_form_template(request)
        if "type_chosen" in request.POST:
            chat_form = form_template(request.POST, request.FILES, user=request.user)

            if chat_form.is_valid():
                new_chat = chat_form.save()
                if new_chat.type == "C":
                    new_chat.members.add(request.user)
                else:
                    new_chat.member2 = request.user
                new_chat.save()
                return redirect(new_chat)
            return render(request, "chat/create_chat.html", {
                'chat_form': chat_form, 'user': request.user
            })

    def get(self, request):
        form_template = self.get_form_template(request)
        chat_form = form_template(user=request.user)
        return render(request, "chat/create_chat.html", {
            'chat_form': chat_form, 'user': request.user
        })


def get_messages_in_chat(m_id):
    try:
        messages = Message.objects.filter(connected_chat_id=m_id)
    except Message.DoesNotExist:
        messages = "No messages yet ..."
    return messages


@method_decorator(permission_required("home.base_permission", raise_exception=True), name="dispatch")
@method_decorator(login_required, name="dispatch")
class ChatDialog(View):

    def get_messages_and_companion(self, request, id, path_name, cur_chat):
        chat_messages = get_messages_in_chat(id)
        for chat_message in chat_messages:
            if chat_message.sender != request.user and not chat_message.is_read:
                chat_message.is_read = True
                chat_message.save()
        message_form = MessageForm()
        if path_name == "dialog":
            if request.user == cur_chat.member1:
                companion = cur_chat.member2
            else:
                companion = cur_chat.member1
        else:
            companion = "-"
        return chat_messages, message_form, companion

    def determine_connected_chat(self, request):
        path_name = request.resolver_match.view_name
        if path_name == "chat":
            return Chat, path_name
        return Dialog, path_name

    def only_alive(self, chat, current_user, chat_name):
        if chat_name == "chat":
            others = chat.members.all()
            if len(others) == 1:
                return True
            return False
        if DELETED_USER == str(chat.member1) or DELETED_USER == str(chat.member2):
            return True
        return False

    def get(self, request, id):
        chat_dialog, path_name = self.determine_connected_chat(request)
        try:
            cur_chat = chat_dialog.objects.get(id=id)
            if (path_name == "dialog" and request.user != cur_chat.member1 and request.user != cur_chat.member2) or \
                    (path_name == "chat" and request.user not in cur_chat.members.all()):
                raise PermissionDenied("Permission Denied")

            chat_messages, message_form, companion = self.get_messages_and_companion(request, id, path_name, cur_chat)
            only_alive = self.only_alive(cur_chat, request.user, path_name)

            return render(request, f"chat/{path_name}.html",
                          {'chat': cur_chat, 'chat_messages': chat_messages, 'companion': companion,
                           'only_alive': only_alive, 'user': request.user, 'message_form': message_form})

        except chat_dialog.DoesNotExist:
            return render(request, f"chat/chat_not_found.html", {'path_name': path_name})
        except PermissionDenied:
            print("Permission Denied")
            return redirect("/")

    def post(self, request, id):
        chat_dialog, path_name = self.determine_connected_chat(request)
        cur_chat = chat_dialog.objects.get(id=id)
        if "send_message" in request.POST:
            text = request.POST.get("text")
            message = Message(content=text, pud_date=timezone.now(), is_read=False, sender=request.user,
                              connected_chat=cur_chat)
            message.save()

        chat_messages, message_form, companion = self.get_messages_and_companion(request, id, path_name, cur_chat)

        return render(request, f"chat/{path_name}.html",
                      {'chat': cur_chat, 'chat_messages': chat_messages, 'companion': companion,
                       'user': request.user, 'message_form': message_form})


def get_profile_data(username):
    data = OurUser.objects.get(username=username)
    return data


@method_decorator(login_required, name="dispatch")
@method_decorator(permission_required("home.base_permission", raise_exception=True), name="dispatch")
class UserProfile(View):

    def get(self, request, username):
        try:
            profile_data = get_profile_data(username)
            if username == DELETED_USER:
                return render(request, "user/user_not_found.html")
            if profile_data.hidden_user and username != str(request.user):
                return render(request, "user/hidden_user.html", {'username': profile_data.username})
            try:
                profile_form = ProfileForm(initial={
                    "first_name": profile_data.first_name,
                    "last_name": profile_data.last_name,
                    "email": profile_data.email,
                    "hidden_user": profile_data.hidden_user
                })
                if str(request.user) != username:
                    raise PermissionDenied("Permission Denied")

                return render(request, "user/own_profile.html", {
                    "data": request.user,
                    "profile_form": profile_form,
                    "user_changed": False})

            except PermissionDenied:
                return render(request, "user/other_profile.html", {"user": request.user, "data": profile_data})
        except OurUser.DoesNotExist:
            return render(request, "user/user_not_found.html")

    def post(self, request, username):
        if "change_profile" in request.POST:
            profile_data = get_profile_data(username)
            profile_data.first_name = request.POST['first_name']
            profile_data.last_name = request.POST['last_name']
            profile_data.email = request.POST['email']
            profile_data.hidden_user = bool(request.POST.get('hidden_user', False))

            user_changed = True

            profile_data.save()

            profile_form = ProfileForm(request.POST, initial={
                "first_name": profile_data.first_name,
                "last_name": profile_data.last_name,
                "email": profile_data.email,
                "hidden_user": profile_data.hidden_user
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
