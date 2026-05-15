from django.db import models  # <--- ESSA LINHA AQUI
from django.contrib.auth.models import User

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    day_of_month = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} - Dia {self.day_of_month}"