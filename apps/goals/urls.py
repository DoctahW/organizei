from django.urls import path

from . import views

app_name = "goals"

urlpatterns = [
    path("", views.goal_list, name="list"),
    path("nova/", views.goal_create, name="create"),
    path("<int:pk>/", views.goal_detail, name="detail"),
    path("<int:pk>/contribuir/", views.goal_contribute, name="contribute"),
]
