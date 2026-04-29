from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from apps.bank_accounts.models import Conta
from .services import build_dashboard_context, get_patrimonio_series

VALID_PERIODS = {"1M", "6M", "1A", "ALL"}


@login_required
def dashboard_home(request):
    context = build_dashboard_context(request.user)
    from django.db.models import Sum, Q
    from django.db.models.functions import Coalesce
    from decimal import Decimal

    registered_accounts = list(
        Conta.objects.filter(usuario=request.user)
        .select_related("bank")
        .annotate(
            total_deposits=Coalesce(Sum('transaction__value', filter=Q(transaction__transaction_type='DEPOSIT')), Decimal('0')),
            total_withdrawals=Coalesce(Sum('transaction__value', filter=Q(transaction__transaction_type='WITHDRAWAL')), Decimal('0'))
        )
        .order_by("-id")[:4]
    )
    for conta in registered_accounts:
        conta.balance = conta.total_deposits - conta.total_withdrawals
    context["registered_accounts"] = registered_accounts
    context["registered_accounts_total"] = len(registered_accounts)
    context["registered_accounts_has_more"] = (
        Conta.objects.filter(usuario=request.user).count() > len(registered_accounts)
    )
    return render(request, "dashboard/index.html", context)


@login_required
def patrimonio_api(request):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" and not request.user.is_authenticated:
        return JsonResponse({"error": "não autenticado"}, status=403)

    period = request.GET.get("period", "1M").upper()
    if period not in VALID_PERIODS:
        return JsonResponse({"error": "period inválido"}, status=400)

    data = get_patrimonio_series(request.user, period)
    return JsonResponse({
        "period": data["period"],
        "current_value": str(data["current_value"]),
        "change_absolute": str(data["change_absolute"]),
        "change_percent": str(data["change_percent"]),
        "series": data["series"],
    })
