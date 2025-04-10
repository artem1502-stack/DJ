from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('registration', views.registration, name="registration"),
    path('login', views.LogInUser.as_view(), name="login"),
    path('logout', views.LogoutUser.as_view(), name="logout"),
    path('create-chat', views.create_chat, name="create-chat"),
    path('chat/<int:id>', views.chat, ),
    path('user/<str:username>', views.user_profile),
    path('<str:username>/change_password', views.change_password)
]
