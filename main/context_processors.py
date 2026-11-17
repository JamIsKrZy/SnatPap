from .models import UserCredit


def user_credits(request):
    """Make user credit balance accessible across templates."""
    if request.user.is_authenticated:
        credit, _ = UserCredit.objects.get_or_create(
            user=request.user,
            defaults={'tokens': 100}
        )
        return {'user_credit': credit}
    return {'user_credit': None}
