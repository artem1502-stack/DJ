from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Chat(models.Model):
    DIALOG = 'D'
    CHAT = 'C'
    CHAT_TYPE_CHOICES = (
        (DIALOG, 'Dialog'),
        (CHAT, 'Chat'))

    type = models.CharField(
        'Тип',
        max_length=1,
        choices=CHAT_TYPE_CHOICES,
        default=CHAT
        )

    name = models.CharField('name', max_length=80)
    members = models.ManyToManyField(User, verbose_name="Choose chat members")

    def get_absolute_url(self):
        return f"/chat/{self.id}"

    def __str__(self):
        m = User.objects.filter(chat__id=self.id)
        s = f"{self.type} \n {m} \n"
        try:
            messages = list(map(str, Message.objects.filter(chat=self.id)))
        except Message.DoesNotExist:
            messages = []
        return s+"\n".join(messages)


class Message(models.Model):
    content = models.TextField("Message")
    pud_date = models.DateTimeField('Date', default=timezone.now)
    is_read = models.BooleanField('Seen', default=False)
    message_id = models.AutoField(unique=True, editable=False, primary_key=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        if self.is_read:
            is_read = '✔️'
        else:
            is_read = '❌'
        return f"{self.sender}: {self.content} ({self.pud_date.strftime('%H:%M')}) {is_read}"
