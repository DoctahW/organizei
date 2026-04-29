from decimal import Decimal, InvalidOperation
from apps.transactions.models import Transaction, Category
from apps.bank_accounts.models import Conta

def validate_transaction_data(form_data, user, get_categories_func):
    errors = {}
    
    if not form_data.get('name'):
        errors['name'] = 'Informe o nome da transação.'
    elif len(form_data['name']) > 150:
        errors['name'] = 'O nome deve ter no máximo 150 caracteres.'

    allowed_types = {choice[0] for choice in Transaction.TYPE_CHOICES}
    if form_data.get('transaction_type') not in allowed_types:
        errors['transaction_type'] = 'Selecione um tipo de transação válido.'

    category = None
    if form_data.get('category_id'):
        try:
            category = get_categories_func(user).get(pk=form_data['category_id'])
        except Category.DoesNotExist:
            errors['category_id'] = 'Selecione uma categoria válida.'

    conta = None
    if form_data.get('conta_id'):
        try:
            conta = Conta.objects.filter(usuario=user).get(pk=form_data['conta_id'])
        except Conta.DoesNotExist:
            errors['conta_id'] = 'Selecione uma conta bancária válida.'

    raw_value = form_data.get('value', '').replace(',', '.')
    try:
        parsed_value = Decimal(raw_value)
        if parsed_value <= 0:
            errors['value'] = 'O valor deve ser maior que zero.'
    except (InvalidOperation, ValueError):
        parsed_value = None
        errors['value'] = 'Informe um valor numérico válido.'

    return errors, parsed_value, category, conta
