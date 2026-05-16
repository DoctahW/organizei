from django.contrib import admin

from .models import Investment


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ("nome", "usuario", "tipo", "ticker", "valor_aplicado", "valor_atual", "cotacao_atualizada_em")
    list_filter = ("tipo",)
    search_fields = ("nome", "ticker", "usuario__username")
