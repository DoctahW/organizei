from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conta, Bank
from .services import validate_bank_account_data


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
    errors = {}

    if request.method == "POST":
        data = {
            "bank": (request.POST.get("bank") or "").strip(),
            "agency": (request.POST.get("agency") or "").strip(),
            "nickname": (request.POST.get("nickname") or "").strip(),
            "number": (request.POST.get("number") or "").strip(),
            "account_type": request.POST.get("account_type") or "corrente"
        }
        
        errors = validate_bank_account_data(data)

        if not errors:
            bank, _ = Bank.objects.get_or_create(name=data["bank"])

            Conta.objects.create(
                usuario=request.user,
                bank=bank,
                account_type=data["account_type"],
                agency=data["agency"],
                nickname=data["nickname"],
                number=data["number"],
            )
            return redirect("bank_accounts")
        
        # se tiver erros, vamos manter os dados preenchidos e mostrar o account_type correto
        account_type = data["account_type"]

    return render(request, 'bank_accounts/register_manual.html', {
        'account_type': account_type,
        'errors': errors,
    })


@login_required
def delete_account(request, account_id):
    conta = get_object_or_404(Conta, id=account_id, usuario=request.user)

    if request.method == "POST":
        conta.delete()

    return redirect("bank_accounts")
