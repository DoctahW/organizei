from apps.bank_accounts.models import Conta

def validate_bank_account_data(data):
    errors = {}
    
    if not data.get("bank"):
        errors["bank"] = "O nome do banco é obrigatório."
        
    if not data.get("number"):
        errors["number"] = "O número da conta é obrigatório."
        
    allowed_types = {choice[0] for choice in Conta.TYPE_CHOICES}
    if data.get("account_type") not in allowed_types:
        errors["account_type"] = "Selecione um tipo de conta válido."

    return errors
