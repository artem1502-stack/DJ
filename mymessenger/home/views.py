from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Message, Chat
from .forms import MessageForm, UserRegistrationForm, UserLogInForm, ChatForm
from django.db import models
from django.contrib.auth.decorators import permission_required
import sqlite3
import datetime


def get_messages():
    con = sqlite3.connect("./db.sqlite3")
    cur = con.cursor()
    cur.execute("SELECT * FROM home_message")
    return cur.fetchall()


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


def save_input_message(request):
    if request.method == "POST":
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


@login_required(login_url="/login")
def index(requests):
    save_input_message(requests)
    # chats = get_chats(requests.user)
    chats = Chat.objects.filter(members=requests.user)

    return render(requests, 'home/index.html', {
        'chats': chats,
        'user': requests.user
    })


def registration(requests):
    save_input_message(requests)
    # messages = get_messages2()

    if requests.method == "POST":
        user_form = UserRegistrationForm(requests.POST)

        if user_form.is_valid():
            new_user = user_form.save()
            new_user.set_password(user_form.cleaned_data["password"])
            new_user.save()
    user_registration_form = UserRegistrationForm()
    # message_form = MessageForm()

    users = User.objects.all()
    return render(requests, "registration/registration.html", {'user_registration_form': user_registration_form,
                                                               'users': users})


def create_chat(requests):
    chat_form = ChatForm()
    choose_type = True
    if requests.method == "POST" and "type_chosen" in requests.POST:
        chat_form = ChatForm(requests.POST)

        if chat_form.is_valid():
            new_chat = chat_form.save()
            new_chat.save()
            return redirect(new_chat)
        return HttpResponse("Incorrect input (error while creating a chat)")
    # if requests.method == "POST" and "type_chosen" in requests.POST:
    #     choose_type = False
    #     type = requests.POST.get("type")
    #     return render(requests, "chat/create-chat.html", {
    #         'chat_form': chat_form, 'user': requests.user, 'choose_type': choose_type, 'type': type
    #     })
    return render(requests, "chat/create-chat.html", {
        'chat_form': chat_form, 'user': requests.user, 'choose_type': choose_type
    })


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
        if requests.method == "POST" and "send_message" in requests.POST:
            try:
                text = requests.POST.get("text")
                message = Message(content=text, pud_date=timezone.now(), is_read=False, sender=requests.user, chat=cur_chat)
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


class LogInUser(LoginView):
    next_page = '/'
    form_class = UserLogInForm
    template_name = "logIn/logIn.html"


class LogoutUser(LogoutView):
    # form_class = UserLogoutForm
    template_name = "logout/logout.html"
