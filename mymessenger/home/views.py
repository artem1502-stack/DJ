from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib.auth import login
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.views import View
from .models import OurUser, Message, Dialog, Chat, DELETED_USER
from .forms import MessageForm, UserLoginForm, ChatForm, DialogForm, ProfileForm
from .fields import RegistrationSerializer
from rest_framework.generics import CreateAPIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status


@method_decorator(login_required, name="dispatch")
class Index(View):
    """
    Displays the main page with chats and users.
    """
    template_name = "home/index.html"

    def get(self, request):
        # Gets all chat, which are connected to the user
        chats = Chat.objects.filter(Q(multichat__members=request.user)
                                    | Q(dialog__member1=request.user) | Q(dialog__member2=request.user))
        return render(request, self.template_name, {
            'chats': chats,
            'user': request.user
        })


class Registration(CreateAPIView):
    """
    Registrate users with tokens.
    """
    serializer_class = RegistrationSerializer
    model = OurUser
    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request, *args, **kwargs):
        # Passes user's input data through serializer (aka rest forms).
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
                return Response(data, status=status.HTTP_201_CREATED, template_name="registration/registration.html")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateChatOrDialog(View):
    """
    Lets users create chats & dialogs.
    """
    template_name = "chat/create_chat.html"

    def get_form_template(self, request):
        """
        Returns connected form depending on the request
        """
        if request.resolver_match.view_name == "create_chat":
            return ChatForm
        return DialogForm

    def add_current_user(self, new_chat, user):
        """
        Adds the current user to the chat/dialog.
        """
        error = ""

        # Checks if the user is creating a chat or a dialog.
        if new_chat.type == "C":
            # Append the current user to "members" field.
            new_chat.members.add(user)
        else:
            # Assign the current user to "member2" field.
            new_chat.member2 = user

            # Check if such a dialog with the same users already exists
            if Dialog.objects.filter(member1=new_chat.member1, member2=new_chat.member2).exists() \
                    or Dialog.objects.filter(member2=new_chat.member1, member1=new_chat.member2).exists():
                error = "Dialog with this person already exists!"
                new_chat.delete()
        return new_chat, error

    def post(self, request):
        form_template = self.get_form_template(request)

        if "type_chosen" in request.POST:
            chat_form = form_template(request.POST, request.FILES, user=request.user)

            if chat_form.is_valid():
                new_chat = chat_form.save()

                new_chat, error = self.add_current_user(new_chat, request.user)

                # If error is not equal to an empty string, the user is attempting to create an already existing dialog.
                if error != "":
                    return render(request, self.template_name, {
                        'chat_form': chat_form, 'user': request.user, 'error': error
                    })

                new_chat.save()
                return redirect(new_chat)

            return render(request, self.template_name, {
                'chat_form': chat_form, 'user': request.user
            })

    def get(self, request):
        form_template = self.get_form_template(request)
        chat_form = form_template(user=request.user)
        return render(request, self.template_name, {
            'chat_form': chat_form, 'user': request.user
        })


def get_messages_in_chat(m_id):
    """
    Gets all messages by a chat id
    """
    try:
        messages = Message.objects.filter(connected_chat_id=m_id)
    except Message.DoesNotExist:
        messages = "No messages yet ..."
    return messages


class ChatDialogView(View):
    """
    Displays a certain chat/dialog with messages and users.
    """

    def get_messages(self, request, id):
        """
        Returns all connected messages
        """
        chat_messages = get_messages_in_chat(id)

        for chat_message in chat_messages:
            # Check if message is read.
            if chat_message.sender != request.user and not chat_message.is_read:
                chat_message.is_read = True
                chat_message.save()

        return chat_messages

    def only_alive(self, chat):
        """
        Check if the current user is the only user left.
        """
        return False

    def post_message(self, request, cur_chat):
        """
        Saves user's message
        """
        text = request.POST.get("text")
        message = Message(content=text, pud_date=timezone.now(), is_read=False, sender=request.user,
                          connected_chat=cur_chat)
        message.save()
        cur_chat.last_message = message
        cur_chat.save()

    def mutual_get(self, request, id, cur_chat, template_name, companion):
        """
        A get method, which can be used for all child classes.
        """
        chat_messages = self.get_messages(request, id)
        only_alive = self.only_alive(cur_chat)
        message_form = MessageForm()

        return render(request, template_name,
                      {'chat': cur_chat, 'chat_messages': chat_messages, 'companion': companion,
                       'only_alive': only_alive, 'user': request.user, 'message_form': message_form})

    def mutual_post(self, request, id, chat_type, template_name, companion):
        """
        A post method, which can be used for all child classes.
        """
        cur_chat = chat_type.objects.get(id=id)
        if "send_message" in request.POST:
            self.post_message(request, cur_chat)

        chat_messages = self.get_messages(request, id)
        message_form = MessageForm()

        return render(request, template_name,
                      {'chat': cur_chat, 'chat_messages': chat_messages, 'companion': companion,
                       'user': request.user, 'message_form': message_form})


@method_decorator(login_required, name="dispatch")
class ChatView(ChatDialogView):
    """
    Displays a certain chat with messages and users.
    """
    template_name = "chat/chat.html"

    def only_alive(self, chat):
        others = chat.members.all()
        return len(others) == 1

    def get(self, request, id):
        try:
            cur_chat = Chat.objects.get(id=id)

            if request.user not in cur_chat.members.all():
                raise PermissionDenied("Permission Denied")

            return self.mutual_get(
                request=request,
                id=id,
                cur_chat=cur_chat,
                template_name=self.template_name,
                companion=""
            )

        except Chat.DoesNotExist:
            return render(request, f"chat/chat_not_found.html", {'path_name': "chat"})

        except PermissionDenied:
            print("Permission Denied")
            return redirect("/")

    def post(self, request, id):
        return self.mutual_post(
            request=request,
            id=id,
            chat_type=Chat,
            template_name=self.template_name,
            companion=""
        )


@method_decorator(login_required, name="dispatch")
class DialogView(ChatDialogView):
    """
    Displays a certain chat with messages and users.
    """
    template_name = "chat/dialog.html"

    def get_companion(self, user, cur_chat):
        """
        Determines the username of the other person in their dialog.
        """
        if user == cur_chat.member1:
            return cur_chat.member2
        return cur_chat.member1

    def only_alive(self, chat):
        return DELETED_USER == str(chat.member1) or DELETED_USER == str(chat.member2)

    def get(self, request, id):
        try:
            cur_chat = Dialog.objects.get(id=id)

            if request.user != cur_chat.member1 and request.user != cur_chat.member2:
                raise PermissionDenied("Permission Denied")

            return self.mutual_get(
                request=request,
                id=id,
                cur_chat=cur_chat,
                template_name=self.template_name,
                companion=self.get_companion(request.user, cur_chat)
            )

        except Dialog.DoesNotExist:
            return render(request, f"chat/chat_not_found.html", {'path_name': "dialog"})

        except PermissionDenied:
            print("Permission Denied")
            return redirect("/")

    def post(self, request, id):
        return self.mutual_post(
            request=request,
            id=id,
            chat_type=Dialog,
            template_name=self.template_name,
            companion=self.get_companion(request.user, Dialog.objects.get(id=id))
        )


class DeleteOrNot(View):
    """
    Asks the user whether they would like to delete their chat.
    """
    def get(self, request, id):
        return render(request, "chat/delete_chat.html", {'id': id})


class Delete(View):
    """
    Removes the user from their chat.
    """
    def get(self, request, id):
        Chat.objects.get(id=id).members.remove(request.user)
        return redirect("/")


def get_profile_data(username):
    """
    Get user's profile data.
    """
    data = OurUser.objects.get(username=username)
    return data


@method_decorator(login_required, name="dispatch")
@method_decorator(permission_required("home.base_permission", raise_exception=True), name="dispatch")
class UserProfile(View):
    """
    Shows user's profile
    """

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
    """
    Changes the password.
    """
    template_name = "user/change_password.html"
    username = None

    def get_object(self):
        """
        Returns user object.
        """
        self.username = str(self.request.user)
        return super().get_object()


@method_decorator(login_required, name="dispatch")
class PasswordChangeDone(View):
    """
    Redirects the user back to their profile.
    """
    def get(self, request):
        return redirect(reverse_lazy("user_profile", kwargs={"username": request.user}))


class LoginUser(LoginView):
    """
    Logs users in
    """
    next_page = '/'
    form_class = UserLoginForm
    template_name = "login/login.html"


class LogoutUser(LogoutView):
    """
    Logs users out
    """
    next_page = '/login'
    template_name = "login/login.html"
