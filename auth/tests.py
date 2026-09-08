from django.contrib.auth.models import User
from django.test import TestCase

from .models import UserProfile


class AuthFlowTests(TestCase):
	def test_registration_creates_user_profile_and_logs_user_in(self):
		response = self.client.post('/auth/register/', {
			'username': 'sam',
			'email': 'sam@example.com',
			'number': '123456789',
			'location': 'London',
			'password': 'A-strong-password-123',
			'password_confirmation': 'A-strong-password-123',
			'consent': 'on',
		})

		self.assertRedirects(response, '/')
		user = User.objects.get(username='sam')
		self.assertTrue(user.is_authenticated)
		self.assertEqual(UserProfile.objects.get(user=user).location, 'London')

	def test_login_accepts_valid_credentials(self):
		User.objects.create_user(username='sam', password='A-strong-password-123')

		response = self.client.post('/auth/login/', {
			'username': 'sam',
			'password': 'A-strong-password-123',
		})

		self.assertRedirects(response, '/')
