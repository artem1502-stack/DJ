from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('registration', views.registration, name="registration"),
    path('login', views.LogInUser.as_view(), name="login"),
    path('logout', views.LogoutUser.as_view(), name="logout"),
    path('chat/<int:chat_id>', views.chat, )
]
