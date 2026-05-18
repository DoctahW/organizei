from django.urls import path

from . import views

app_name = "onboarding"

urlpatterns = [
    path("", views.start, name="start"),
    path("bank-account/", views.step_bank_account, name="step_bank_account"),
    path("transaction/", views.step_transaction, name="step_transaction"),
    path("investment/", views.step_investment, name="step_investment"),
    path("investment/manual/", views.step_investment_manual, name="step_investment_manual"),
    path("investment/auto/", views.step_investment_auto, name="step_investment_auto"),
    path("investment/tesouro/", views.step_investment_tesouro, name="step_investment_tesouro"),
    path("subscription/", views.step_subscription, name="step_subscription"),
    path("finish/", views.finish, name="finish"),
]
