# Integração com o CSV público do Tesouro Transparente.
# O endpoint é grátis, sem chave, e atualizado diariamente em D-1.

import csv
from datetime import date, datetime, timedelta
from decimal import Decimal

import requests
from django.db import transaction
from django.utils import timezone

from .models import TesouroPrecoHistorico, TesouroTitulo

CSV_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"
)
FETCH_TIMEOUT = 30
STALE_AFTER = timedelta(hours=24)

TICKER_PREFIX = "TD"  # ex: "TD|Tesouro IPCA+|2032-08-15"


def _parse_date(raw):
    return datetime.strptime(raw.strip(), "%d/%m/%Y").date()


def _parse_decimal(raw):
    return Decimal(raw.strip().replace(".", "").replace(",", "."))


def _iter_csv_rows():
    """Faz streaming do CSV e yielda dicts parseados (todas as linhas, todas as datas)."""
    response = requests.get(CSV_URL, timeout=FETCH_TIMEOUT, stream=True)
    response.raise_for_status()
    response.encoding = "utf-8"

    reader = csv.DictReader(response.iter_lines(decode_unicode=True), delimiter=";")
    for row in reader:
        try:
            yield {
                "tipo": row["Tipo Titulo"].strip(),
                "vencimento": _parse_date(row["Data Vencimento"]),
                "data": _parse_date(row["Data Base"]),
                "pu_compra": _parse_decimal(row["PU Compra Manha"]),
                "pu_venda": _parse_decimal(row["PU Venda Manha"]),
                "taxa_compra": _parse_decimal(row["Taxa Compra Manha"]),
            }
        except (KeyError, ValueError, ArithmeticError):
            continue


def sync_from_csv():
    """Baixa CSV do Tesouro Transparente e faz upsert no DB.

    Atualiza TesouroTitulo e popula TesouroPrecoHistorico
    incrementalmente (só linhas novas).

    Retorna (titulos_criados, titulos_atualizados, historico_novo).
    """
    today = date.today()
    latest = {}  # (tipo, venc) -> dict com data_base mais recente

    # Carrega chaves já existentes no histórico pra fazer insert incremental
    existing_history = set(
        TesouroPrecoHistorico.objects.values_list("tipo", "vencimento", "data")
    )

    historico_batch = []

    for row in _iter_csv_rows():
        key = (row["tipo"], row["vencimento"])

        # Histórico: insert se ainda não existe
        hkey = (row["tipo"], row["vencimento"], row["data"])
        if hkey not in existing_history:
            historico_batch.append(TesouroPrecoHistorico(
                tipo=row["tipo"],
                vencimento=row["vencimento"],
                data=row["data"],
                pu_compra=row["pu_compra"],
                pu_venda=row["pu_venda"],
            ))
            existing_history.add(hkey)

        # Snapshot atual: só títulos ainda vivos, mantém o de Data Base mais recente
        if row["vencimento"] < today:
            continue
        existing = latest.get(key)
        if existing is None or existing["data"] < row["data"]:
            latest[key] = row

    criados = 0
    atualizados = 0

    with transaction.atomic():
        for row in latest.values():
            _, created = TesouroTitulo.objects.update_or_create(
                tipo=row["tipo"],
                vencimento=row["vencimento"],
                defaults={
                    "data_base": row["data"],
                    "pu_compra": row["pu_compra"],
                    "pu_venda": row["pu_venda"],
                    "taxa_compra": row["taxa_compra"],
                },
            )
            if created:
                criados += 1
            else:
                atualizados += 1

        keys_no_csv = set(latest.keys())
        for existing in TesouroTitulo.objects.all():
            if (existing.tipo, existing.vencimento) not in keys_no_csv:
                existing.delete()

        # Bulk insert do histórico em chunks
        if historico_batch:
            TesouroPrecoHistorico.objects.bulk_create(historico_batch, batch_size=2000)

    return criados, atualizados, len(historico_batch)


def _is_stale():
    latest = TesouroTitulo.objects.order_by("-updated_at").values_list("updated_at", flat=True).first()
    if latest is None:
        return True
    return (timezone.now() - latest) > STALE_AFTER


def ensure_fresh():
    """Sincroniza com CSV apenas se o DB estiver vazio ou desatualizado (>24h)."""
    if _is_stale():
        sync_from_csv()


def list_available_titles():
    """Lista todos os títulos do snapshot atual. Faz lazy refresh se necessário."""
    ensure_fresh()
    return list(TesouroTitulo.objects.all())


def get_current_pu(tipo, vencimento_iso):
    ensure_fresh()
    vencimento = date.fromisoformat(vencimento_iso)
    try:
        titulo = TesouroTitulo.objects.get(tipo=tipo, vencimento=vencimento)
    except TesouroTitulo.DoesNotExist as exc:
        raise ValueError(f"Título não encontrado: {tipo} {vencimento_iso}") from exc
    return titulo.pu_compra


def get_pu_on_date(tipo, vencimento_iso, data_alvo, *, side="venda"):
    """Retorna o PU do título numa data específica.

    Se a data exata não existe (fim de semana, feriado), busca o último dia útil
    anterior disponível.

    Levanta ValueError se não há nenhum registro até a data alvo.
    """
    ensure_fresh()
    vencimento = date.fromisoformat(vencimento_iso) if isinstance(vencimento_iso, str) else vencimento_iso
    field = "pu_venda" if side == "venda" else "pu_compra"
    registro = (
        TesouroPrecoHistorico.objects
        .filter(tipo=tipo, vencimento=vencimento, data__lte=data_alvo)
        .order_by("-data")
        .values("data", field)
        .first()
    )
    if registro is None:
        raise ValueError(
            f"Sem PU disponível para {tipo} venc {vencimento_iso} em {data_alvo}. "
            "Verifique se a data não é anterior à existência do título."
        )
    return registro[field]


def make_ticker(tipo, vencimento_iso):
    return f"{TICKER_PREFIX}|{tipo}|{vencimento_iso}"


def parse_ticker(ticker):
    """Retorna (tipo, vencimento_iso) se for ticker do Tesouro, senão None."""
    if not ticker or not ticker.startswith(f"{TICKER_PREFIX}|"):
        return None
    parts = ticker.split("|", 2)
    if len(parts) != 3:
        return None
    return parts[1], parts[2]
