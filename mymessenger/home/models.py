from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Message(models.Model):
    content = models.TextField("Message")
    pud_date = models.DateTimeField('Date', default=timezone.now)
    is_read = models.BooleanField('Seen', default=False)

    def __str__(self):
        return f"Content: {self.content} | Published at: {self.pud_date} | Is read or not: {self.is_read}"


# class Chat(models.Model):
# 	DIALOG = 'D'
# 	CHAT = 'C'
# 	CHAT_TYPE_CHOICES = (
# 		(DIALOG, 'Dialog'),
# 		(CHAT, 'Chat'))
#
# 	type_ = models.CharField(
# 		('Тип'),
# 		max_length=1,
# 		choices=CHAT_TYPE_CHOICES,
# 		default=DIALOG
# 		)
# 	members = models.ManyToManyField(User, verbose_name=("Участник"))
#
# 	@models.permalink
# 	def get_absolute_url(self):
# 		return 'users:messages', (), {'chat_id': self.pk}
