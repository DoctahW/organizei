from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.auth_view, name="login"),
    path("register/", views.auth_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("password_change/", views.password_change_view, name="password_change"),
    path(
        "password_change/done/",
        views.password_change_done_view,
        name="password_change_done",
    ),
]
