from django.urls import path
from . import views

app_name = "subscriptions"

urlpatterns = [
    path('assinaturas/', views.manage_subscriptions, name='manage_subscriptions'),
    path('assinaturas/deletar/<int:pk>/', views.delete_subscription, name='delete_subscription'),
    path('assinaturas/<int:pk>/', views.subscription_detail, name='subscription_detail'),
]
