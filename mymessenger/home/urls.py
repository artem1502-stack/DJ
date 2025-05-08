from django.urls import path
from . import views

urlpatterns = [
    path('', views.Index.as_view(), name="index"),
    path('registration', views.registration, name="registration"),
    path('login', views.LoginUser.as_view(), name="login"),
    path('logout', views.LogoutUser.as_view(), name="logout"),
    path('create_chat', views.CreateChatOrDialog.as_view(), name="create_chat"),
    path('create_dialog', views.CreateChatOrDialog.as_view(), name="create_dialog"),
    path('chat/<int:id>', views.ChatDialog.as_view(), name="chat"),
    path('dialog/<int:id>', views.ChatDialog.as_view(), name="dialog"),
    path('user/<str:username>', views.UserProfile.as_view(), name="user_profile"),
    path('<str:username>/change_password', views.ChangePassword.as_view(), name="change_password"),
    path('password_change_done', views.PasswordChangeDone.as_view(), name="password_change_done")
]
