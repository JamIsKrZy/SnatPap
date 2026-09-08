from django.conf import settings
from django.db import models


class UserProfile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	country_code = models.CharField(max_length=6, default='+63')
	phone_number = models.CharField(max_length=30, blank=True)
	street_address = models.CharField(max_length=255, blank=True)
	barangay = models.CharField(max_length=150, blank=True)
	city_municipality = models.CharField(max_length=150, blank=True)
	province = models.CharField(max_length=150, blank=True)
	postal_code = models.CharField(max_length=20, blank=True)
	consent = models.BooleanField(default=False)

	def __str__(self):
		return self.user.username
