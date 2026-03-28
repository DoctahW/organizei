from django.urls import path
from . import views

app_name = "transactions"

urlpatterns = [
    path("", views.get_transactions, name="get_transactions"), #buscar as transações
    path("create/", views.create_transactions, name="create_transaction"), #criar uma nova transação
    path('', views.get_transactions, name="get_transactions"), #exibir as transações do sistema
    path('post/', views.post_transaction, name="post_transaction"), # enviar uma transação
    #path("<int:pk>/", views.transaction_detail, name="detail"), #detalhes da transação
    #path("<int:pk>/edit/", views.transaction_update, name="update"), #atualizar a transação
    #path("<int:pk>/delete/", views.transaction_delete, name="delete"), #deletar a transação
]
