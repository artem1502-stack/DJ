from django.contrib.auth.models import Permission
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login
from django.views import View
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from .models import OurUser, Message, Dialog, Chat, DELETED_USER
from .forms import MessageForm, UserRegistrationForm, UserLoginForm, ChatForm, DialogForm, ProfileForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from .fields import OurUserSerializer, RegistrationSerializer
import datetime


def get_messages2():
    messages = Message.objects.all()
    return messages


@method_decorator(login_required, name="dispatch")
class Index(View):
    def get(self, request):
        chats = Chat.objects.filter(Q(multichat__members=request.user)\
            | Q(dialog__member1=request.user) | Q(dialog__member2=request.user))
        return render(request, 'home/index.html', {
            'chats': chats,
            'user': request.user
        })

# works properly if user is registered?
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response


# class CustomAuthToken(APIView):
#     serializer_class = OurUserSerializer
#     model = OurUser
#     permission_classes = [
#         permissions.AllowAny
#     ]
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllUsers(APIView):
    # authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def __init__(self):
        super().__init__()
        self.serializer_class = OurUserSerializer

    def get(self, request):
        queryset = OurUser.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


from rest_framework import permissions
from rest_framework.generics import CreateAPIView
from rest_framework import status
from rest_framework.authtoken.models import Token


class Registration(CreateAPIView):
    serializer_class = RegistrationSerializer
    model = OurUser
    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            new_user = serializer.save()

            permission = Permission.objects.get(
                codename="base_permission"
            )
            new_user.user_permissions.add(permission)

            new_user.save()
            data = dict(serializer.data)
            if new_user is not None:
                login(request, new_user)
                data["token"] = Token.objects.create(user=new_user).key
                print(data)
                return Response\
                    (data, status=status.HTTP_201_CREATED, template_name="registration/registration.html")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
                    if Dialog.objects.filter(member1=new_chat.member1, member2=new_chat.member2).exists() \
                            or Dialog.objects.filter(member2=new_chat.member1, member1=new_chat.member2).exists():
                        error = "Dialog with this person already exists!"
                        new_chat.delete()
                        return render(request, "chat/create_chat.html", {
                            'chat_form': chat_form, 'user': request.user, 'error': error
                        })
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
            cur_chat.last_message = message
            cur_chat.save()

        chat_messages, message_form, companion = self.get_messages_and_companion(request, id, path_name, cur_chat)

        return render(request, f"chat/{path_name}.html",
                      {'chat': cur_chat, 'chat_messages': chat_messages, 'companion': companion,
                       'user': request.user, 'message_form': message_form})


class DeleteOrNot(View):
    def get(self, request, id):
        return render(request, "chat/delete_chat.html", {'id': id})


class Delete(View):
    def get(self, request, id):
        cur_chat = Chat.objects.get(id=id).members.remove(request.user)
        return redirect("/")


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


# rest authentication
class LoginUser(LoginView):
    next_page = '/'
    form_class = UserLoginForm
    template_name = "login/login.html"


class LogoutUser(LogoutView):
    next_page = '/login'
    template_name = "login/login.html"
