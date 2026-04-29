from decimal import Decimal, InvalidOperation

def validate_goal_data(data):
    errors = {}
    amount = None

    if not data.get("name"):
        errors["name"] = "Nome da meta é obrigatório."

    try:
        amount = Decimal(data.get("target_amount", ""))
        if amount <= 0:
            errors["target_amount"] = "O valor deve ser maior que zero."
    except (InvalidOperation, ValueError):
        errors["target_amount"] = "Informe um valor válido."

    if not data.get("deadline"):
        errors["deadline"] = "Data limite é obrigatória."

    return errors, amount

def validate_contribution_data(data):
    errors = {}
    amount = None

    try:
        amount = Decimal(data.get("amount", ""))
        if amount <= 0:
            errors["amount"] = "O valor deve ser maior que zero."
    except (InvalidOperation, ValueError):
        errors["amount"] = "Informe um valor válido."

    if not data.get("date"):
        errors["date"] = "Data é obrigatória."

    return errors, amount
