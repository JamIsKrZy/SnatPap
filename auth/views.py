from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import UserProfile


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

	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		email = request.POST.get('email', '').strip()
		number = request.POST.get('number', '').strip()
		location = request.POST.get('location', '').strip()
		password = request.POST.get('password', '')
		password_confirmation = request.POST.get('password_confirmation', '')
		consent = request.POST.get('consent') == 'on'

		errors = []
		if not username or not email or not number or not location or not password:
			errors.append('Please complete every field.')
		if User.objects.filter(username=username).exists():
			errors.append('That username is already in use.')
		if User.objects.filter(email=email).exists():
			errors.append('That email address is already registered.')
		if password != password_confirmation:
			errors.append('The passwords do not match.')
		if not consent:
			errors.append('You must agree to the consent statement.')

		if not errors:
			with transaction.atomic():
				user = User.objects.create_user(username=username, email=email, password=password)
				UserProfile.objects.create(
					user=user,
					number=number,
					location=location,
					consent=consent,
				)
			login(request, user)
			return redirect('home')

		for error in errors:
			messages.error(request, error)

	return render(request, 'auth/register.html')


@require_POST
def logout_view(request):
	logout(request)
	return redirect('login')

# Create your views here.
