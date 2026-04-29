from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conta, Bank


from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from decimal import Decimal

@login_required
def accounts_list(request):
    contas = Conta.objects.filter(usuario=request.user).select_related("bank").annotate(
        total_deposits=Coalesce(Sum('transaction__value', filter=Q(transaction__transaction_type='DEPOSIT')), Decimal('0')),
        total_withdrawals=Coalesce(Sum('transaction__value', filter=Q(transaction__transaction_type='WITHDRAWAL')), Decimal('0'))
    )
    for conta in contas:
        conta.balance = conta.total_deposits - conta.total_withdrawals

    return render(request, 'bank_accounts/myaccounts.html', {
        'contas': contas,
    })

@login_required
def register_account(request):
    if request.method == "POST":
        method = request.POST.get("method")

        if method == "manual":
            return redirect("register_manual")

        elif method == "automatic":
            return redirect("register_auto")

    return render(request, "bank_accounts/register_account.html")

@login_required
def register_auto(request):
    return render(request, 'bank_accounts/register_auto.html')

@login_required
def register_manual(request):
    account_type = request.GET.get('type') or 'corrente'

    if request.method == "POST":
        bank_name = (request.POST.get("bank") or "").strip()
        agency = (request.POST.get("agency") or "").strip()
        nickname = (request.POST.get("nickname") or "").strip()
        number = (request.POST.get("number") or "").strip()
        account_type = request.POST.get("account_type") or "corrente"

        bank, _ = Bank.objects.get_or_create(name=bank_name)

        Conta.objects.create(
            usuario=request.user,
            bank=bank,
            account_type=account_type,
            agency=agency,
            nickname=nickname,
            number=number,
        )
        return redirect("bank_accounts")

    return render(request, 'bank_accounts/register_manual.html', {
        'account_type': account_type,
    })


@login_required
def delete_account(request, account_id):
    conta = get_object_or_404(Conta, id=account_id, usuario=request.user)

    if request.method == "POST":
        conta.delete()

    return redirect("bank_accounts")
