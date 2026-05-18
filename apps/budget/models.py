from django.db import models
from django.contrib.auth.models import User
from apps.transactions.models import Category

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    month = models.DateField()
    limit = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('user', 'month', 'category')
        
    def __str__(self):
        return f"{self.user} - {self.category.name} - {self.month.strftime('%m/%Y')}"