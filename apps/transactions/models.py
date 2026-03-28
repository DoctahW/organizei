from django.db import models

class Transaction(models.Model):
    # Definição dos tipos
    TYPE_CHOICES = [
        ('DEPOSIT', 'Entrada'),
        ('WITHDRAWAL', 'Saída'),
    ]
    # Campos de uma transação (provisórios)
    name = models.CharField(max_length=150, verbose_name="Descrição")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    transaction_type = models.CharField(
        max_length=10, 
        choices=TYPE_CHOICES, 
        verbose_name="Tipo de Transação"
    ) 
    date = models.DateField(auto_now_add=True, verbose_name="Data") 

    def __str__(self):
        return f"{self.name} - R$ {self.value} ({self.get_transaction_type_display()})"
