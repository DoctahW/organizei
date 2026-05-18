from collections import defaultdict
from datetime import date as date_cls, datetime
from decimal import Decimal

import requests
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.bank_accounts.models import Bank, Conta
from apps.bank_accounts.services import validate_bank_account_data
from apps.investments import tesouro
from apps.investments.models import Investment, InvestmentMovimentacao
from apps.investments.services import (
    fetch_brapi_quote,
    validate_auto_data,
    validate_manual_data,
    validate_tesouro_data,
)
from apps.subscriptions.models import Subscription
from apps.subscriptions.views import _create_transactions_for_subscription
from apps.transactions.models import Transaction
from apps.transactions.services import validate_transaction_data
from apps.transactions.views import _get_categories_for_user


def _user_has_account(user):
    return Conta.objects.filter(usuario=user).exists()


@login_required
def start(request):
    if not _user_has_account(request.user):
        return redirect("onboarding:step_bank_account")
    return redirect("onboarding:step_transaction")


@login_required
def step_bank_account(request):
    if _user_has_account(request.user):
        return redirect("onboarding:step_transaction")

    account_type = request.GET.get("type") or "corrente"
    errors = {}
    form_data = {}

    if request.method == "POST":
        form_data = {
            "bank": (request.POST.get("bank") or "").strip(),
            "agency": (request.POST.get("agency") or "").strip(),
            "nickname": (request.POST.get("nickname") or "").strip(),
            "number": (request.POST.get("number") or "").strip(),
            "account_type": request.POST.get("account_type") or "corrente",
        }
        errors = validate_bank_account_data(form_data)

        if not errors:
            bank, _ = Bank.objects.get_or_create(name=form_data["bank"])
            Conta.objects.create(
                usuario=request.user,
                bank=bank,
                account_type=form_data["account_type"],
                agency=form_data["agency"],
                nickname=form_data["nickname"],
                number=form_data["number"],
            )
            return redirect("onboarding:step_transaction")

        account_type = form_data["account_type"]

    return render(
        request,
        "onboarding/step_bank_account.html",
        {
            "step_index": 1,
            "step_total": 4,
            "account_type": account_type,
            "errors": errors,
            "form_data": form_data,
        },
    )


@login_required
def step_transaction(request):
    if not _user_has_account(request.user):
        return redirect("onboarding:step_bank_account")

    contas = Conta.objects.filter(usuario=request.user)
    categories = _get_categories_for_user(request.user)
    errors = {}
    form_data = {}

    if request.method == "POST":
        form_data = {
            "name": request.POST.get("name", "").strip(),
            "transaction_type": request.POST.get("transaction_type", "").strip(),
            "value": request.POST.get("value", "").strip(),
            "category_id": request.POST.get("category_id", "").strip(),
            "conta_id": request.POST.get("conta_id", "").strip(),
            "date": request.POST.get("date", "").strip(),
        }

        errors, parsed_value, category, conta = validate_transaction_data(
            form_data, request.user, _get_categories_for_user
        )

        if not errors:
            extra_kwargs = {}
            if form_data["date"]:
                extra_kwargs["date"] = form_data["date"]
            Transaction.objects.create(
                user=request.user,
                name=form_data["name"],
                transaction_type=form_data["transaction_type"],
                value=parsed_value,
                category=category,
                conta=conta,
                is_fixed=False,
                **extra_kwargs,
            )
            return redirect("onboarding:step_investment")

    return render(
        request,
        "onboarding/step_transaction.html",
        {
            "step_index": 2,
            "step_total": 4,
            "contas": contas,
            "categories": categories,
            "transaction_type_choices": Transaction.TYPE_CHOICES,
            "errors": errors,
            "form_data": form_data,
        },
    )


@login_required
def step_investment(request):
    if not _user_has_account(request.user):
        return redirect("onboarding:step_bank_account")

    return render(
        request,
        "onboarding/step_investment.html",
        {"step_index": 3, "step_total": 4},
    )


@login_required
def step_investment_manual(request):
    if not _user_has_account(request.user):
        return redirect("onboarding:step_bank_account")

    errors = {}
    data = {}

    if request.method == "POST":
        data = {
            "nome": (request.POST.get("nome") or "").strip(),
            "tipo": request.POST.get("tipo") or "",
            "valor_aplicado": request.POST.get("valor_aplicado"),
            "valor_atual": request.POST.get("valor_atual"),
            "data_aplicacao": (request.POST.get("data_aplicacao") or "").strip(),
        }
        errors, valor_aplicado, valor_atual = validate_manual_data(data)

        if not errors:
            with db_transaction.atomic():
                investimento = Investment.objects.create(
                    usuario=request.user,
                    nome=data["nome"],
                    tipo=data["tipo"],
                    ticker="",
                    pu_atual=valor_atual,
                )
                InvestmentMovimentacao.objects.create(
                    investment=investimento,
                    tipo="compra",
                    data=data["data_aplicacao"],
                    valor=valor_aplicado,
                    quantidade=Decimal("1"),
                    pu_na_data=valor_aplicado,
                    observacao="Aplicação inicial",
                )
                investimento.recalc()
            return redirect("onboarding:step_subscription")

    return render(
        request,
        "onboarding/step_investment_manual.html",
        {"step_index": 3, "step_total": 4, "errors": errors, "data": data},
    )


@login_required
def step_investment_auto(request):
    if not _user_has_account(request.user):
        return redirect("onboarding:step_bank_account")

    errors = {}
    data = {}

    if request.method == "POST":
        data = {
            "tipo": request.POST.get("tipo") or "",
            "ticker": (request.POST.get("ticker") or "").strip(),
            "quantidade": request.POST.get("quantidade"),
            "valor_aplicado": request.POST.get("valor_aplicado"),
            "data_aplicacao": (request.POST.get("data_aplicacao") or "").strip(),
        }
        errors, ticker, quantidade, valor_aplicado = validate_auto_data(data)

        if not errors:
            try:
                price = fetch_brapi_quote(ticker)
            except (requests.RequestException, ValueError, KeyError) as exc:
                errors["ticker"] = f"Não foi possível consultar a cotação de {ticker}: {exc}"
            else:
                pu_na_compra = (valor_aplicado / quantidade).quantize(Decimal("0.0001"))
                with db_transaction.atomic():
                    investimento = Investment.objects.create(
                        usuario=request.user,
                        nome=ticker,
                        tipo=data["tipo"],
                        ticker=ticker,
                        pu_atual=price,
                        cotacao_atualizada_em=timezone.now(),
                    )
                    InvestmentMovimentacao.objects.create(
                        investment=investimento,
                        tipo="compra",
                        data=data["data_aplicacao"],
                        valor=valor_aplicado,
                        quantidade=quantidade,
                        pu_na_data=pu_na_compra,
                        observacao="Aplicação inicial",
                    )
                    investimento.recalc()
                return redirect("onboarding:step_subscription")

    return render(
        request,
        "onboarding/step_investment_auto.html",
        {"step_index": 3, "step_total": 4, "errors": errors, "data": data},
    )


@login_required
def step_investment_tesouro(request):
    if not _user_has_account(request.user):
        return redirect("onboarding:step_bank_account")

    errors = {}
    data = {}

    try:
        titulos = tesouro.list_available_titles()
    except requests.RequestException as exc:
        messages.error(
            request,
            f"Não foi possível carregar a lista do Tesouro Direto agora ({exc}). Tente novamente em instantes.",
        )
        return redirect("onboarding:step_investment")

    titulos_por_tipo = defaultdict(list)
    for t in titulos:
        titulos_por_tipo[t.tipo].append({
            "vencimento": t.vencimento.isoformat(),
            "vencimento_br": t.vencimento.strftime("%d/%m/%Y"),
            "pu_compra": str(t.pu_compra.quantize(Decimal("0.01"))),
            "taxa_compra": str(t.taxa_compra.quantize(Decimal("0.01"))),
        })
    tipos = sorted(titulos_por_tipo.keys())
    titulos_dict = dict(titulos_por_tipo)

    if request.method == "POST":
        data = {
            "tipo_tesouro": (request.POST.get("tipo_tesouro") or "").strip(),
            "vencimento": (request.POST.get("vencimento") or "").strip(),
            "valor_aplicado": request.POST.get("valor_aplicado"),
            "data_aplicacao": (request.POST.get("data_aplicacao") or "").strip(),
        }
        errors, tipo, vencimento, valor_aplicado = validate_tesouro_data(data)

        if not errors:
            try:
                data_compra = date_cls.fromisoformat(data["data_aplicacao"])
                pu_compra = tesouro.get_pu_on_date(tipo, vencimento, data_compra, side="venda")
                pu_atual = tesouro.get_current_pu(tipo, vencimento)
            except (ValueError, requests.RequestException) as exc:
                errors["vencimento"] = f"Não foi possível buscar o PU do título: {exc}"
            else:
                quantidade = (valor_aplicado / pu_compra).quantize(Decimal("0.0001"))
                ticker = tesouro.make_ticker(tipo, vencimento)
                nome = f"{tipo} {vencimento[0:4]}"
                with db_transaction.atomic():
                    investimento = Investment.objects.create(
                        usuario=request.user,
                        nome=nome,
                        tipo="tesouro",
                        ticker=ticker,
                        pu_atual=pu_atual,
                        cotacao_atualizada_em=timezone.now(),
                    )
                    InvestmentMovimentacao.objects.create(
                        investment=investimento,
                        tipo="compra",
                        data=data_compra,
                        valor=valor_aplicado,
                        quantidade=quantidade,
                        pu_na_data=pu_compra,
                        observacao=f"Compra inicial (PU da data: R$ {pu_compra})",
                    )
                    investimento.recalc()
                return redirect("onboarding:step_subscription")

    return render(
        request,
        "onboarding/step_investment_tesouro.html",
        {
            "step_index": 3,
            "step_total": 4,
            "errors": errors,
            "data": data,
            "tipos": tipos,
            "titulos_dict": titulos_dict,
        },
    )


@login_required
def step_subscription(request):
    if not _user_has_account(request.user):
        return redirect("onboarding:step_bank_account")

    contas = Conta.objects.filter(usuario=request.user)
    errors = {}
    form_data = {}

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        raw_value = (request.POST.get("value") or "").replace("R$", "").replace(".", "").replace(",", ".").strip()
        start_date_raw = (request.POST.get("start_date") or "").strip()
        conta_id = (request.POST.get("conta_id") or "").strip()

        form_data = {
            "name": name,
            "value": request.POST.get("value", ""),
            "start_date": start_date_raw,
            "conta_id": conta_id,
        }

        if not name:
            errors["name"] = "Informe o nome da assinatura."
        try:
            from decimal import Decimal, InvalidOperation
            value = Decimal(raw_value)
            if value <= 0:
                errors["value"] = "O valor deve ser maior que zero."
        except (InvalidOperation, ValueError):
            value = None
            errors["value"] = "Informe um valor numérico válido."

        try:
            start_date_input = (
                datetime.strptime(start_date_raw, "%Y-%m-%d").date()
                if start_date_raw
                else date_cls.today()
            )
        except ValueError:
            start_date_input = None
            errors["start_date"] = "Informe uma data válida."

        conta = None
        if conta_id:
            try:
                conta = Conta.objects.filter(usuario=request.user).get(pk=conta_id)
            except Conta.DoesNotExist:
                errors["conta_id"] = "Selecione uma conta bancária válida."
        else:
            errors["conta_id"] = "Selecione uma conta bancária."

        if not errors:
            subscription = Subscription.objects.create(
                user=request.user,
                name=name,
                value=value,
                start_date=start_date_input,
                end_date=None,
                conta=conta,
            )
            _create_transactions_for_subscription(subscription, request.user, conta)
            return redirect("onboarding:finish")

    return render(
        request,
        "onboarding/step_subscription.html",
        {
            "step_index": 4,
            "step_total": 4,
            "contas": contas,
            "errors": errors,
            "form_data": form_data,
        },
    )


@login_required
def finish(request):
    return redirect("dashboard:home")
