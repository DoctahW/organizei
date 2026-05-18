from datetime import date as date_cls
from decimal import Decimal

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from django.http import JsonResponse

from .models import Investment, InvestmentMovimentacao, TesouroPrecoHistorico
from .services import (
    QUOTE_RATE_LIMIT_SECONDS,
    fetch_brapi_quote,
    validate_auto_data,
    validate_manual_data,
    validate_tesouro_data,
)
from . import tesouro


@login_required
def investment_list(request):
    investimentos = Investment.objects.filter(usuario=request.user)

    totals = investimentos.aggregate(
        total_aplicado=Sum("valor_aplicado"),
        total_atual=Sum("valor_atual"),
    )
    total_aplicado = totals["total_aplicado"] or Decimal("0.00")
    total_atual = totals["total_atual"] or Decimal("0.00")
    rendimento_total = total_atual - total_aplicado
    rentabilidade_total = (
        (rendimento_total / total_aplicado * Decimal("100")).quantize(Decimal("0.01"))
        if total_aplicado > 0
        else Decimal("0.00")
    )

    return render(request, "investments/list.html", {
        "investimentos": investimentos,
        "total_aplicado": total_aplicado,
        "total_atual": total_atual,
        "rendimento_total": rendimento_total,
        "rentabilidade_total": rentabilidade_total,
    })


def _resolve_next(request):
    candidate = request.POST.get("next") or request.GET.get("next") or ""
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}
    ):
        return candidate
    return None


@login_required
def investment_register(request):
    return render(request, "investments/register.html", {"next": _resolve_next(request) or ""})


@login_required
def investment_create_manual(request):
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
            with transaction.atomic():
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
            messages.success(request, f'Investimento "{investimento.nome}" cadastrado.')
            next_url = _resolve_next(request)
            return redirect(next_url) if next_url else redirect("investments:list")

    return render(request, "investments/register_manual.html", {"errors": errors, "data": data, "next": _resolve_next(request) or ""})


@login_required
def investment_create_auto(request):
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
                with transaction.atomic():
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
                messages.success(
                    request,
                    f"{investimento.ticker} cadastrado (cotação atual R$ {price}).",
                )
                next_url = _resolve_next(request)
                return redirect(next_url) if next_url else redirect("investments:list")

    return render(request, "investments/register_auto.html", {"errors": errors, "data": data, "next": _resolve_next(request) or ""})


@login_required
def investment_create_tesouro(request):
    from collections import defaultdict

    errors = {}
    data = {}

    try:
        titulos = tesouro.list_available_titles()
    except requests.RequestException as exc:
        messages.error(
            request,
            f"Não foi possível carregar a lista do Tesouro Direto agora ({exc}). Tente novamente em instantes.",
        )
        return redirect("investments:register")

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
                with transaction.atomic():
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
                messages.success(
                    request,
                    f"{investimento.nome} cadastrado: {quantidade} títulos "
                    f"comprados a R$ {pu_compra} cada (PU atual R$ {pu_atual}).",
                )
                next_url = _resolve_next(request)
                return redirect(next_url) if next_url else redirect("investments:list")

    return render(
        request,
        "investments/register_tesouro.html",
        {
            "errors": errors,
            "data": data,
            "tipos": tipos,
            "titulos_dict": titulos_dict,
            "next": _resolve_next(request) or "",
        },
    )


def _add_movimentacao(request, pk, tipo_mov):
    """Adiciona uma compra (aporte) ou venda (resgate) a um investimento existente."""
    investimento = get_object_or_404(Investment, pk=pk, usuario=request.user)

    if request.method != "POST":
        return redirect("investments:detail", pk=pk)

    raw_data = (request.POST.get("data") or "").strip()
    raw_valor = (request.POST.get("valor") or "").strip()
    raw_qtd = (request.POST.get("quantidade") or "").strip()
    observacao = (request.POST.get("observacao") or "").strip()[:200]

    if not raw_data or not raw_valor:
        messages.error(request, "Data e valor são obrigatórios.")
        return redirect("investments:detail", pk=pk)

    try:
        data_mov = date_cls.fromisoformat(raw_data)
        valor = Decimal(raw_valor)
        if valor <= 0:
            raise ValueError("Valor deve ser maior que zero.")
    except (ValueError, ArithmeticError) as exc:
        messages.error(request, f"Dados inválidos: {exc}")
        return redirect("investments:detail", pk=pk)

    tesouro_key = tesouro.parse_ticker(investimento.ticker)
    quantidade = None
    pu_na_data = None

    try:
        if tesouro_key:
            tipo, vencimento = tesouro_key
            side = "venda" if tipo_mov == "compra" else "compra"
            pu_na_data = tesouro.get_pu_on_date(tipo, vencimento, data_mov, side=side)
            quantidade = (valor / pu_na_data).quantize(Decimal("0.0001"))
        elif investimento.ticker:
            # Ações/FIIs/cripto: usuário precisa informar a quantidade
            if not raw_qtd:
                messages.error(request, "Para ações/FIIs/cripto, informe a quantidade.")
                return redirect("investments:detail", pk=pk)
            quantidade = Decimal(raw_qtd)
            if quantidade <= 0:
                raise ValueError("Quantidade deve ser maior que zero.")
            pu_na_data = (valor / quantidade).quantize(Decimal("0.0001"))
        else:
            # Manual: quantidade simbólica
            quantidade = Decimal("1") if tipo_mov == "compra" else Decimal("0")
            pu_na_data = valor
    except (ValueError, ArithmeticError, requests.RequestException) as exc:
        messages.error(request, f"Não foi possível calcular: {exc}")
        return redirect("investments:detail", pk=pk)

    if tipo_mov == "venda" and quantidade > investimento.quantidade:
        messages.error(
            request,
            f"Você só tem {investimento.quantidade} títulos/cotas — não dá para resgatar {quantidade}.",
        )
        return redirect("investments:detail", pk=pk)

    with transaction.atomic():
        InvestmentMovimentacao.objects.create(
            investment=investimento,
            tipo=tipo_mov,
            data=data_mov,
            valor=valor,
            quantidade=quantidade,
            pu_na_data=pu_na_data,
            observacao=observacao,
        )
        investimento.recalc()

    label = "Aporte" if tipo_mov == "compra" else "Resgate"
    messages.success(request, f"{label} de R$ {valor} registrado.")
    return redirect("investments:detail", pk=pk)


@login_required
def investment_detail(request, pk):
    investimento = get_object_or_404(
        Investment.objects.prefetch_related("movimentacoes"),
        pk=pk,
        usuario=request.user,
    )
    is_tesouro = bool(tesouro.parse_ticker(investimento.ticker))
    is_brapi = bool(investimento.ticker) and not is_tesouro
    return render(request, "investments/detail.html", {
        "investimento": investimento,
        "movimentacoes": investimento.movimentacoes.all(),
        "is_tesouro": is_tesouro,
        "is_brapi": is_brapi,
        "hoje": date_cls.today().isoformat(),
    })


@login_required
def investment_history(request, pk):
    """Retorna JSON com a série histórica (valor da posição × custo acumulado)."""
    investimento = get_object_or_404(Investment, pk=pk, usuario=request.user)
    movs = list(investimento.movimentacoes.order_by("data", "created_at"))
    if not movs:
        return JsonResponse({"points": [], "tipo": "vazio"})

    primeira_data = movs[0].data
    tesouro_key = tesouro.parse_ticker(investimento.ticker)

    points = []

    if tesouro_key:
        tipo, vencimento_iso = tesouro_key
        from datetime import date as _date
        vencimento = _date.fromisoformat(vencimento_iso)
        serie = TesouroPrecoHistorico.objects.filter(
            tipo=tipo,
            vencimento=vencimento,
            data__gte=primeira_data,
        ).order_by("data").values("data", "pu_venda")

        qtd = Decimal("0")
        custo = Decimal("0")
        mov_idx = 0
        for h in serie:
            while mov_idx < len(movs) and movs[mov_idx].data <= h["data"]:
                m = movs[mov_idx]
                if m.tipo == "compra":
                    qtd += m.quantidade
                    custo += m.valor
                else:
                    qtd -= m.quantidade
                    custo -= m.valor
                mov_idx += 1
            valor = (qtd * h["pu_venda"]).quantize(Decimal("0.01"))
            points.append({
                "date": h["data"].isoformat(),
                "valor": float(valor),
                "custo": float(custo),
            })
        serie_tipo = "tesouro"
    else:
        # Sem histórico granular: 2 pontos (primeira compra → hoje)
        qtd = Decimal("0")
        custo = Decimal("0")
        for m in movs:
            if m.tipo == "compra":
                qtd += m.quantidade
                custo += m.valor
            else:
                qtd -= m.quantidade
                custo -= m.valor
            points.append({
                "date": m.data.isoformat(),
                "valor": float(custo),  # sem PU intermediário, valor = custo até hoje
                "custo": float(custo),
            })
        # Ponto final = valor atual de hoje
        if investimento.cotacao_atualizada_em:
            today_iso = timezone.localtime(investimento.cotacao_atualizada_em).date().isoformat()
        else:
            today_iso = date_cls.today().isoformat()
        points.append({
            "date": today_iso,
            "valor": float(investimento.valor_atual),
            "custo": float(investimento.valor_aplicado),
        })
        serie_tipo = "esparso"

    return JsonResponse({
        "points": points,
        "tipo": serie_tipo,
        "nome": investimento.nome,
    })


@login_required
def investment_add_aporte(request, pk):
    return _add_movimentacao(request, pk, "compra")


@login_required
def investment_add_resgate(request, pk):
    return _add_movimentacao(request, pk, "venda")


@login_required
def investment_delete(request, pk):
    investimento = get_object_or_404(Investment, pk=pk, usuario=request.user)
    if request.method == "POST":
        nome = investimento.nome
        investimento.delete()
        messages.success(request, f'Investimento "{nome}" removido.')
    return redirect("investments:list")


@login_required
def investment_update_quote(request, pk):
    investimento = get_object_or_404(Investment, pk=pk, usuario=request.user)

    if request.method != "POST":
        return redirect("investments:list")

    if not investimento.ticker:
        messages.warning(request, "Este investimento não possui ticker para atualização automática.")
        return redirect("investments:list")

    if investimento.cotacao_atualizada_em:
        elapsed = (timezone.now() - investimento.cotacao_atualizada_em).total_seconds()
        if elapsed < QUOTE_RATE_LIMIT_SECONDS:
            wait = int(QUOTE_RATE_LIMIT_SECONDS - elapsed)
            messages.warning(
                request,
                f"Aguarde {wait}s antes de atualizar a cotação de {investimento.ticker} novamente.",
            )
            return redirect("investments:list")

    tesouro_key = tesouro.parse_ticker(investimento.ticker)

    try:
        if tesouro_key:
            tipo, vencimento = tesouro_key
            price = tesouro.get_current_pu(tipo, vencimento)
            display = f"{tipo} {vencimento}"
        else:
            price = fetch_brapi_quote(investimento.ticker)
            display = investimento.ticker
    except (requests.RequestException, ValueError, KeyError) as exc:
        last = investimento.cotacao_atualizada_em
        msg = f"Não foi possível atualizar a cotação de {investimento.ticker} agora."
        if last:
            msg += f" Última atualização: {timezone.localtime(last):%d/%m/%Y %H:%M}."
        msg += f" (detalhe: {exc})"
        messages.warning(request, msg)
        return redirect("investments:list")

    investimento.pu_atual = price
    investimento.cotacao_atualizada_em = timezone.now()
    investimento.save(update_fields=["pu_atual", "cotacao_atualizada_em"])
    investimento.recalc()
    messages.success(
        request,
        f"Cotação de {display} atualizada para R$ {price} (total: R$ {investimento.valor_atual}).",
    )
    return redirect("investments:list")
