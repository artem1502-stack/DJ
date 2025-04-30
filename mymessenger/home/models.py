from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from polymorphic.models import PolymorphicModel


class Chat(PolymorphicModel):
    class Meta:
        ...


class Multichat(Chat):
    type = "C"
    name = models.CharField('name', max_length=80)
    members = models.ManyToManyField(User, verbose_name="Choose chat members")

    def get_absolute_url(self):
        return f"/chat/{self.id}"

    def __str__(self):
        m = User.objects.filter(multichat__id=self.id)
        s = f"{self.type} \n {m} \n"
        try:
            messages = list(map(str, Message.objects.filter(multichat=self.id)))
        except Message.DoesNotExist:
            messages = []
        return s+"\n".join(messages)


class Dialog(Chat):
    type = "D"
    name = ""
    member1 = models.ForeignKey(User, verbose_name="Choose a user", on_delete=models.CASCADE, related_name="companion")
    member2 = models.ForeignKey(User, verbose_name="YOU", on_delete=models.CASCADE, related_name="you")
    # pk = models.CompositePrimaryKey("member1_id", "member2_id")
    # id = models.AutoField(primary_key=True)

    def get_absolute_url(self):
        return f"/dialog/{self.id}"

    def clean(self):
        if self.member1 == self.member2 or self.member1 is None or self.member2 is None:
            raise ValidationError("member1 == member2 or one of the values is None")

    def __str__(self):
        m = User.objects.filter(dialog__id=self.id)
        s = f"{self.type} \n {m} \n {self.member2} AND {self.member1}"
        try:
            messages = list(map(str, Message.objects.filter(dialog=self.id)))
        except Message.DoesNotExist:
            messages = []
        return s+"\n".join(messages)


class Message(models.Model):
    content = models.TextField("Message")
    pud_date = models.DateTimeField('Date', default=timezone.now)
    is_read = models.BooleanField('Seen', default=False)
    message_id = models.AutoField(unique=True, editable=False, primary_key=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    # dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE, blank=True, null=True, default=None)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        if self.is_read:
            is_read = '✔️'
        else:
            is_read = '❌'
        return f"{self.sender}: {self.content} ({self.pud_date.strftime('%H:%M')}) {is_read}"
