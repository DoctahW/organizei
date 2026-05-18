from django.urls import path

from . import views

app_name = "investments"

urlpatterns = [
    path("", views.investment_list, name="list"),
    path("novo/", views.investment_register, name="register"),
    path("novo/manual/", views.investment_create_manual, name="create_manual"),
    path("novo/automatico/", views.investment_create_auto, name="create_auto"),
    path("novo/tesouro/", views.investment_create_tesouro, name="create_tesouro"),
    path("<int:pk>/", views.investment_detail, name="detail"),
    path("<int:pk>/historico/", views.investment_history, name="history"),
    path("<int:pk>/aporte/", views.investment_add_aporte, name="add_aporte"),
    path("<int:pk>/resgate/", views.investment_add_resgate, name="add_resgate"),
    path("<int:pk>/atualizar-cotacao/", views.investment_update_quote, name="update_quote"),
    path("<int:pk>/excluir/", views.investment_delete, name="delete"),
]
