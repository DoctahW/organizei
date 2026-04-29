from decimal import Decimal, InvalidOperation

def validate_budget_data(data):
    errors = {}
    limit = None
    
    raw_limit = data.get("limit", "").strip()
    if not raw_limit:
        errors["limit"] = "O limite é obrigatório."
    else:
        try:
            limit = Decimal(raw_limit)
            if limit <= 0:
                errors["limit"] = "O limite deve ser maior que zero."
        except (InvalidOperation, ValueError):
            errors["limit"] = "Informe um valor válido."

    return errors, limit
