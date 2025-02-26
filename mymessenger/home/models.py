from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



class Chat(models.Model):
	DIALOG = 'D'
	CHAT = 'C'
	CHAT_TYPE_CHOICES = (
		(DIALOG, 'Dialog'),
		(CHAT, 'Chat'))

	type_ = models.CharField(
		('Тип'),
		max_length=1,
		choices=CHAT_TYPE_CHOICES,
		default=DIALOG
		)
	members = models.ManyToManyField(User, verbose_name=("Участник"))

	@models.permalink
	def get_absolute_url(self):
		return 'users:messages', (), {'chat_id': self.pk}




class Message(models.Model):
	chat = models.ForeignKey(Chat, verbose_name = ("Чат"))
	author = models.ForeignKey(User, verbose_name = ("Пользователь"))
	message = models.TextField(("Сообщение"))
	pud_date = models.DateTimeField(('Дата сообщения'), default=timezone.now)
	is_readed = models.BooleanField(('Прочитано'), default=False)

	class Meta:
		ordering = ['pub_date']

	def __str__(self):
		return self.message
