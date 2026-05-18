import os
from decimal import Decimal, InvalidOperation

import requests


BRAPI_URL = "https://brapi.dev/api/quote/{ticker}"
BRAPI_TIMEOUT = 5
QUOTE_RATE_LIMIT_SECONDS = 60

AUTO_TYPES = {"acao", "fii", "cripto"}
MANUAL_TYPES = {"fundo", "outro"}


def _parse_decimal(raw, field, errors, *, allow_zero=False, required=True):
    raw = (raw or "").strip()
    if not raw:
        if required:
            errors[field] = "Campo obrigatório."
        return None
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        errors[field] = "Informe um valor válido."
        return None
    if value < 0 or (not allow_zero and value == 0):
        errors[field] = "O valor deve ser maior que zero."
        return None
    return value


def validate_manual_data(data):
    errors = {}

    if not data.get("nome"):
        errors["nome"] = "Nome do investimento é obrigatório."

    if data.get("tipo") not in MANUAL_TYPES:
        errors["tipo"] = "Selecione um tipo válido."

    valor_aplicado = _parse_decimal(data.get("valor_aplicado"), "valor_aplicado", errors)
    valor_atual = _parse_decimal(
        data.get("valor_atual"), "valor_atual", errors, allow_zero=True
    )

    if not data.get("data_aplicacao"):
        errors["data_aplicacao"] = "Data de aplicação é obrigatória."

    return errors, valor_aplicado, valor_atual


def validate_auto_data(data):
    errors = {}

    if data.get("tipo") not in AUTO_TYPES:
        errors["tipo"] = "Selecione um tipo válido."

    ticker = (data.get("ticker") or "").strip().upper()
    if not ticker:
        errors["ticker"] = "Ticker é obrigatório."

    quantidade = _parse_decimal(data.get("quantidade"), "quantidade", errors)
    valor_aplicado = _parse_decimal(data.get("valor_aplicado"), "valor_aplicado", errors)

    if not data.get("data_aplicacao"):
        errors["data_aplicacao"] = "Data de aplicação é obrigatória."

    return errors, ticker, quantidade, valor_aplicado


def validate_tesouro_data(data):
    errors = {}

    tipo = (data.get("tipo_tesouro") or "").strip()
    vencimento = (data.get("vencimento") or "").strip()

    if not tipo:
        errors["tipo_tesouro"] = "Selecione o tipo de título."
    if not vencimento:
        errors["vencimento"] = "Selecione o vencimento."

    valor_aplicado = _parse_decimal(data.get("valor_aplicado"), "valor_aplicado", errors)

    if not data.get("data_aplicacao"):
        errors["data_aplicacao"] = "Data de aplicação é obrigatória."

    return errors, tipo, vencimento, valor_aplicado


def fetch_brapi_quote(ticker):
    """Consulta a BRAPI e retorna o preço atual como Decimal.

    Levanta requests.RequestException, ValueError ou KeyError em caso de falha
    (timeout, status != 2xx, ticker inexistente, JSON inesperado, sem cotação).
    """
    token = os.environ.get("BRAPI_TOKEN", "")
    params = {"token": token} if token else {}
    response = requests.get(
        BRAPI_URL.format(ticker=ticker),
        params=params,
        timeout=BRAPI_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()

    results = payload.get("results") or []
    if not results:
        raise ValueError(f"Ticker {ticker} não encontrado")

    price = results[0].get("regularMarketPrice")
    if price is None:
        raise ValueError(f"Cotação indisponível para {ticker}")

    return Decimal(str(price))
