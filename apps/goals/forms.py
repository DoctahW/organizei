from django import forms

from .models import Goal, GoalContribution


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["name", "target_amount", "deadline"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex: Carro Novo, Laptop..."}),
            "target_amount": forms.NumberInput(attrs={"placeholder": "0,00", "step": "0.01"}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "name": "Nome da meta",
            "target_amount": "Valor alvo (R$)",
            "deadline": "Data limite",
        }


class GoalContributionForm(forms.ModelForm):
    class Meta:
        model = GoalContribution
        fields = ["amount", "date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"placeholder": "0,00", "step": "0.01"}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "amount": "Valor (R$)",
            "date": "Data",
        }
