from django.shortcuts import render
from .models import Message
import sqlite3


def get_messages():
    con = sqlite3.connect("./db.sqlite3")
    cur = con.cursor()
    cur.execute("SELECT * FROM home_message")
    return cur.fetchall()


# Create your views here.
def index(requests):
    messages = get_messages()
    return render(requests, 'home/index.html', {'messages': messages})
