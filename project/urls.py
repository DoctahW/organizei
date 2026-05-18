from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return redirect("accounts/login")


urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("transactions/", include("apps.transactions.urls")),
    path("categories/", include("apps.categories.urls")),
    path("investments/", include("apps.investments.urls")),
    path("metas/", include("apps.goals.urls")),
    path("subscriptions/", include("apps.subscriptions.urls")),
    path("budget/", include("apps.budget.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("my_accounts/",include("apps.bank_accounts.urls")),
    path("onboarding/", include("apps.onboarding.urls")),
]
