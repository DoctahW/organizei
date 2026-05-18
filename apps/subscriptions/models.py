from django.db import models  
from django.contrib.auth.models import User
from django.utils import timezone

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(default=timezone.now, verbose_name="Data de Início/Vencimento")
    end_date = models.DateField(blank=True, null=True, verbose_name="Data de Encerramento")
    conta = models.ForeignKey(
        'bank_accounts.Conta',
        on_delete=models.CASCADE,
        verbose_name="Conta Bancária",
    )
    def __str__(self):
        return f"{self.name} - Dia {self.start_date.day}"