from django.contrib.auth.models import User
from django.test import TestCase

from .models import UserProfile


class AuthFlowTests(TestCase):
	def test_registration_page_loads_without_errors(self):
		response = self.client.get('/auth/register/')

		self.assertEqual(response.status_code, 200)

	def test_registration_creates_user_profile_and_logs_user_in(self):
		response = self.client.post('/auth/register/', {
			'first_name': 'Sam',
			'last_name': 'Smith',
			'username': 'sam',
			'email': 'sam@example.com',
			'country_code': '+63',
			'phone_number': '9123456789',
			'street_address': '123 Main Street',
			'barangay': 'Central',
			'city_municipality': 'Manila',
			'province': 'Metro Manila',
			'postal_code': '1000',
			'password': 'A-strong-password-123',
			'password_confirmation': 'A-strong-password-123',
			'consent': 'on',
		})

		self.assertRedirects(response, '/')
		user = User.objects.get(username='sam')
		self.assertTrue(user.is_authenticated)
		self.assertEqual(user.first_name, 'Sam')
		self.assertEqual(user.last_name, 'Smith')
		profile = UserProfile.objects.get(user=user)
		self.assertEqual(profile.country_code, '+63')
		self.assertEqual(profile.phone_number, '9123456789')
		self.assertEqual(profile.street_address, '123 Main Street')
		self.assertEqual(profile.barangay, 'Central')
		self.assertEqual(profile.city_municipality, 'Manila')
		self.assertEqual(profile.province, 'Metro Manila')
		self.assertEqual(profile.postal_code, '1000')

	def test_login_accepts_valid_credentials(self):
		User.objects.create_user(username='sam', password='A-strong-password-123')

		response = self.client.post('/auth/login/', {
			'username': 'sam',
			'password': 'A-strong-password-123',
		})

		self.assertRedirects(response, '/')

	def test_registration_keeps_values_and_highlights_invalid_fields(self):
		response = self.client.post('/auth/register/', {
			'first_name': 'Sam',
			'last_name': 'Smith',
			'username': 'sam',
			'email': 'sam@example.com',
			'country_code': '+63',
			'phone_number': '9123456789',
			'street_address': '123 Main Street',
			'barangay': 'Central',
			'city_municipality': 'Manila',
			'province': 'Metro Manila',
			'postal_code': '1000',
			'password': 'A-strong-password-123',
			'password_confirmation': 'different-password',
		})

		self.assertContains(response, 'value="sam"')
		self.assertContains(response, 'value="sam@example.com"')
		self.assertContains(response, 'class="form-control is-invalid" id="password"', html=False)
		self.assertContains(response, 'class="form-control is-invalid" id="password_confirmation"', html=False)

	def test_registration_keeps_location_values_after_validation_error(self):
		response = self.client.post('/auth/register/', {
			'first_name': 'Sam',
			'last_name': 'Smith',
			'username': 'sam',
			'email': 'sam@example.com',
			'country_code': '+63',
			'phone_number': '9123456789',
			'street_address': '123 Main Street',
			'barangay': 'Central',
			'city_municipality': 'Manila',
			'province': 'Metro Manila',
			'postal_code': '1000',
			'password': 'A-strong-password-123',
			'password_confirmation': 'different-password',
			'consent': 'on',
		})

		html = response.content.decode()
		self.assertIn('data-selected="Metro Manila"', html)
		self.assertIn('data-selected="Manila"', html)
		self.assertIn('data-selected="Central"', html)
		self.assertContains(response, 'The passwords do not match.')

	def test_registration_rejects_invalid_email(self):
		response = self.client.post('/auth/register/', {
			'first_name': 'Sam',
			'last_name': 'Smith',
			'username': 'sam',
			'email': 'not-an-email',
			'country_code': '+63',
			'phone_number': '9123456789',
			'street_address': '123 Main Street',
			'barangay': 'Central',
			'city_municipality': 'Manila',
			'province': 'Metro Manila',
			'postal_code': '1000',
			'password': 'A-strong-password-123',
			'password_confirmation': 'A-strong-password-123',
			'consent': 'on',
		})

		self.assertContains(response, 'Please enter a valid email address.')
		self.assertContains(response, 'class="form-control is-invalid" id="email"', html=False)
