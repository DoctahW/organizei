from django.shortcuts import redirect

from apps.bank_accounts.models import Conta


BYPASS_PREFIXES = (
    "/onboarding/",
    "/accounts/",
    "/admin/",
    "/static/",
    "/my_accounts/",
)


class RequireBankAccountMiddleware:
    """Redirect authenticated users with no bank account into the onboarding wizard."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not request.path.startswith(BYPASS_PREFIXES)
            and not Conta.objects.filter(usuario=user).exists()
        ):
            return redirect("onboarding:step_bank_account")
        return self.get_response(request)
