from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Message, Chat
from .forms import MessageForm, UserRegistrationForm, UserLogInForm
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
    messages = get_messages2()
    message_form = MessageForm()
    return render(requests, 'home/index.html', {
        'messages': messages,
        'message_form': message_form,
        'user': requests.user
        # 'user_is_logged': user_is_logged
    })


def registration(requests):
    save_input_message(requests)
    messages = get_messages2()

    if requests.method == "POST":
        user_form = UserRegistrationForm(requests.POST)

        if user_form.is_valid():
            new_user = user_form.save()
            new_user.set_password(user_form.cleaned_data["password"])
            new_user.save()
    user_registration_form = UserRegistrationForm()
    message_form = MessageForm()

    users = User.objects.all()
    return render(requests, "registration/registration.html", {'user_registration_form': user_registration_form,
                                                               'users': users})


def chat(requests, chat_id):
    try:
        cur_chat = Chat.objects.get(chat_id=chat_id)
        return render(requests, "chat/chat.html", {'chat': cur_chat, 'user': requests.user})
    except Chat.DoesNotExist:
        return HttpResponse("Chat not found")

# def logIn(requests):
#     if requests.method == "POST":
#         logIn_form = UserLogInForm(requests.POST)
#
#         if logIn_form.is_valid():
#             cd = logIn_form.cleaned_data
#             user = authenticate(username=cd["username"], password=cd["password"])
#             if user is not None:
#                 if user.is_active:
#                     login(requests, user)
#                     return HttpResponse("Login successful")
#                 else:
#                     return HttpResponse("Account invalid")
#             else:
#                 return HttpResponse("Username or password incorrect")
#
#     logIn_form = UserLogInForm()
#     return render(requests, "logIn/logIn.html", {'logIn_form': logIn_form, 'logout': logout})


class LogInUser(LoginView):
    next_page = '/'
    form_class = UserLogInForm
    template_name = "logIn/logIn.html"


class LogoutUser(LogoutView):
    # form_class = UserLogoutForm
    template_name = "logout/logout.html"
