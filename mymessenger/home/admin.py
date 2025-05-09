from django.contrib import admin
from .models import Message, Multichat, Dialog, OurUser
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


class OurUsersInline(admin.StackedInline):
    model = OurUser
    can_delete = False
    verbose_name_plural = "our_users"


class UserAdmin(BaseUserAdmin):
    inlines = [OurUsersInline]


admin.site.register(User, UserAdmin)
admin.site.register(OurUser)
admin.site.register(Message)
admin.site.register(Multichat)
admin.site.register(Dialog)
