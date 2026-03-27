from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/", include("apps.accounts.urls")),
    path("transactions/", include("apps.transactions.urls")),
    path("categories/", include("apps.categories.urls")),
    path("investments/", include("apps.investments.urls")),
    path("metas/", include("apps.goals.urls")),
    path("subscriptions/", include("apps.subscriptions.urls")),
]
