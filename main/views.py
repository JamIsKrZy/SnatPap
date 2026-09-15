from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
	return render(request, 'main/home.html')


@login_required
def profile_view(request):
	return render(request, 'profile.html')


@login_required
def settings_view(request):
	return render(request, 'settings.html')
