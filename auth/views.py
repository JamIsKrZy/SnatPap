from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import UserProfile

COUNTRY_CODES = [
	('+63', '🇵🇭'),
	('+1', '🇺🇸'),
	('+1', '🇨🇦'),
	('+44', '🇬🇧'),
	('+61', '🇦🇺'),
	('+81', '🇯🇵'),
	('+82', '🇰🇷'),
	('+91', '🇮🇳'),
	('+60', '🇲🇾'),
	('+65', '🇸🇬'),
]


def login_view(request):
	if request.user.is_authenticated:
		return redirect('home')

	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		password = request.POST.get('password', '')
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			return redirect('home')
		messages.error(request, 'The username or password is incorrect.')

	return render(request, 'auth/login.html')


def register_view(request):
	if request.user.is_authenticated:
		return redirect('home')

	field_errors = set()
	if request.method == 'POST':
		first_name = request.POST.get('first_name', '').strip()
		last_name = request.POST.get('last_name', '').strip()
		username = request.POST.get('username', '').strip()
		email = request.POST.get('email', '').strip()
		country_code = request.POST.get('country_code', '+63').strip()
		phone_number = request.POST.get('phone_number', '').strip()
		street_address = request.POST.get('street_address', '').strip()
		barangay = request.POST.get('barangay', '').strip()
		city_municipality = request.POST.get('city_municipality', '').strip()
		province = request.POST.get('province', '').strip()
		postal_code = request.POST.get('postal_code', '').strip()
		password = request.POST.get('password', '')
		password_confirmation = request.POST.get('password_confirmation', '')
		consent = request.POST.get('consent') == 'on'

		errors = []
		if not first_name or not last_name or not username or not email or not phone_number or not street_address or not barangay or not city_municipality or not province or not postal_code or not password:
			errors.append('Please complete every field.')
			for field in ('first_name', 'last_name', 'username', 'email', 'phone_number', 'street_address', 'barangay', 'city_municipality', 'province', 'postal_code', 'password'):
				if not request.POST.get(field, '').strip():
					field_errors.add(field)
		if email:
			try:
				validate_email(email)
			except ValidationError:
				errors.append('Please enter a valid email address.')
				field_errors.add('email')
		if User.objects.filter(username=username).exists():
			errors.append('That username is already in use.')
			field_errors.add('username')
		if User.objects.filter(email=email).exists():
			errors.append('That email address is already registered.')
			field_errors.add('email')
		if password != password_confirmation:
			errors.append('The passwords do not match.')
			field_errors.update(('password', 'password_confirmation'))
		if not consent:
			errors.append('You must agree to the consent statement.')
			field_errors.add('consent')

		if not errors:
			with transaction.atomic():
				user = User.objects.create_user(
					username=username,
					first_name=first_name,
					last_name=last_name,
					email=email,
					password=password,
				)
				UserProfile.objects.create(
					user=user,
					country_code=country_code,
					phone_number=phone_number,
					street_address=street_address,
					barangay=barangay,
					city_municipality=city_municipality,
					province=province,
					postal_code=postal_code,
					consent=consent,
				)
			login(request, user)
			return redirect('home')

		for error in errors:
			messages.error(request, error)

	return render(request, 'auth/register.html', {
		'country_codes': COUNTRY_CODES,
		'form_data': request.POST,
		'field_errors': field_errors,
	})


@require_POST
def logout_view(request):
	logout(request)
	return redirect('login')

# Create your views here.
