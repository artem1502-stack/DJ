from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.utils import timezone
from polymorphic.models import PolymorphicModel
from django.contrib.auth.models import AbstractUser

DELETED_USER = "Deleted User"


def get_sentinel_user():
    user = get_user_model().objects.get_or_create(username=DELETED_USER)[0]
    # user.is_active = False
    # user.save()
    return user


class OurUser(AbstractUser):
    hidden_user = models.BooleanField(default=False)
    verbose_name = "user"

    class Meta:
        permissions = [
            ("base_permission", "All basic permissions of a user"),
            ("admin_permission", "All basic permissions of an admin")
        ]


class ChatManager(models.Manager):
    def get_chat_by_member(self, member):
        chats = Chat.objects.all()
        lst = []
        for chat in chats:
            if member in chat.get_members():
                lst.append(chat)
        return lst


class Chat(PolymorphicModel):
    last_message = models.OneToOneField(
        "Message",
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def __str__(self):
        try:
            messages = list(map(str, Message.objects.filter(connected_chat__id=self.id)))
        except Message.DoesNotExist:
            messages = []
        return " || Messages: " + ", \n".join(messages)

    def get_members(self):
        pass

    def update_last_message(self):
        self.last_message = Message.objects.filter(connected_chat__id=self.id).latest("pub_date")

    class Meta:
        ...


class Multichat(Chat):
    type = "C"
    name = models.CharField('name', max_length=80)
    members = models.ManyToManyField(OurUser, verbose_name="Choose chat members")
    # ex_members = models.ManyToManyField(OurUser, blank=True)

    def get_absolute_url(self):
        return f"/chat/{self.id}"

    def get_members(self):
        return OurUser.objects.filter(username__in=self.members)

    def __str__(self):
        m = list(map(str, self.members.all()))
        s = f"Type: {self.type} || Name: {self.name} || \n Members: {', '.join(m)} \n"
        return s + super().__str__()


class Dialog(Chat):
    type = "D"
    name = ""
    member1 = models.ForeignKey(OurUser, verbose_name="Choose a user", on_delete=models.SET(get_sentinel_user),
                                null=True, related_name="companion")
    member2 = models.ForeignKey(OurUser, verbose_name="YOU", on_delete=models.SET(get_sentinel_user), null=True,
                                related_name="you")

    def get_absolute_url(self):
        return f"/dialog/{self.id}"

    def get_members(self):
        m1 = OurUser.objects.get(self.member1)
        m2 = OurUser.objects.get(self.member2)
        return m1 | m2

    def __str__(self):
        s = f"Type: {self.type} || \n Members: {self.member2}, {self.member1}"
        return s + super().__str__()


class Message(models.Model):
    content = models.TextField("Message")
    pud_date = models.DateTimeField('Date', default=timezone.now)
    is_read = models.BooleanField('Seen', default=False)
    message_id = models.AutoField(unique=True, editable=False, primary_key=True)
    connected_chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(OurUser, on_delete=models.SET(get_sentinel_user), null=True)

    def __str__(self):
        if self.is_read:
            is_read = '✔️'
        else:
            is_read = '❌'
        return f"{self.sender}: {self.content} ({self.pud_date.strftime('%H:%M')}) {is_read}"
