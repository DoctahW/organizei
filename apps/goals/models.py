from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum


class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals")
    name = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    deadline = models.DateField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def current_amount(self):
        total = self.contributions.aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0.00")

    @property
    def progress_percent(self):
        if self.target_amount == 0:
            return 0
        percent = (self.current_amount / self.target_amount) * 100
        return min(round(float(percent), 1), 100)

    def check_completion(self):
        """Mark as completed if progress reached 100%. Returns True if just completed."""
        if self.progress_percent >= 100 and not self.is_completed:
            self.is_completed = True
            self.save(update_fields=["is_completed"])
            return True
        return False


class GoalContribution(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="contributions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.goal.name} — R$ {self.amount}"
