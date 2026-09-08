from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = (
		'user',
		'phone_number',
		'city_municipality',
		'province',
		'consent',
	)
	list_filter = ('consent', 'province', 'city_municipality')
	search_fields = (
		'user__username',
		'user__email',
		'user__first_name',
		'user__last_name',
		'phone_number',
		'street_address',
		'barangay',
		'city_municipality',
		'province',
		'postal_code',
	)
	list_select_related = ('user',)
	fieldsets = (
		('Account', {
			'fields': ('user', 'consent'),
		}),
		('Contact', {
			'fields': ('country_code', 'phone_number'),
		}),
		('Address', {
			'fields': (
				'street_address',
				'barangay',
				'city_municipality',
				'province',
				'postal_code',
			),
		}),
	)
