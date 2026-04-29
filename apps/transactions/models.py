from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Usuário",
    )
    name = models.CharField(max_length=100, verbose_name="Nome")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.name

    @property
    def is_global(self):
        return self.user is None


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('DEPOSIT', 'Entrada'),
        ('WITHDRAWAL', 'Saída'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150, verbose_name="Descrição")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    transaction_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Tipo de Transação"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoria",
    )
    conta = models.ForeignKey(
        'bank_accounts.Conta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Conta Bancária",
    )
    date = models.DateField(auto_now_add=True, verbose_name="Data")

    def __str__(self):
        return f"{self.name} - R$ {self.value} ({self.get_transaction_type_display()})"