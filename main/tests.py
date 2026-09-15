from django.contrib.auth import get_user_model
from django.test import TestCase


class HomePageTests(TestCase):
	def test_home_page_is_available(self):
		response = self.client.get('/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Home page')

	def test_authenticated_home_page_shows_profile_dropdown(self):
		user = get_user_model().objects.create_user(username='alice', password='pass123')
		self.client.force_login(user)

		response = self.client.get('/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'View profile')
		self.assertContains(response, 'Settings')
		self.assertContains(response, 'Log out')

	def test_profile_and_settings_pages_are_available(self):
		user = get_user_model().objects.create_user(username='alice', password='pass123')
		self.client.force_login(user)

		profile_response = self.client.get('/profile/')
		settings_response = self.client.get('/settings/')

		self.assertEqual(profile_response.status_code, 200)
		self.assertContains(profile_response, 'Profile')
		self.assertEqual(settings_response.status_code, 200)
		self.assertContains(settings_response, 'Settings')
