from django.conf import settings
from django.db import models


class UserProfile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	number = models.CharField(max_length=30)
	location = models.CharField(max_length=150)
	consent = models.BooleanField(default=False)

	def __str__(self):
		return self.user.username
