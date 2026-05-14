from datetime import date, timedelta
from itertools import groupby

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.dateformat import format as date_fmt
from .models import Transaction, Category
from django.db.models import Sum, Q
from apps.bank_accounts.models import Conta
from .services import validate_transaction_data

def _get_categories_for_user(user):
    return Category.objects.filter(Q(user=None) | Q(user=user)).order_by('name')


def _build_create_transaction_context(user, form_data=None, errors=None):
    totais = Transaction.objects.filter(user=user).aggregate(
        e=Sum('value', filter=Q(transaction_type='DEPOSIT')),
        s=Sum('value', filter=Q(transaction_type='WITHDRAWAL'))
    )
    account_balance = (totais['e'] or 0) - (totais['s'] or 0)
    contas = Conta.objects.filter(usuario=user)
    return {
        'form_data': form_data or {},
        'errors': errors or {},
        'account_balance': account_balance,
        'transaction_type_choices': Transaction.TYPE_CHOICES,
        'categories': _get_categories_for_user(user),
        'contas': contas,
    }


# exibir o formulário para criar uma nova transação
@login_required
# to do: criar uma funcao de adicionar uma nova categoria
def create_category(request):
    return render(request, 'transactions/create_category.html')

@login_required
def create_transactions(request):
    if request.method == 'POST':
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'transaction_type': request.POST.get('transaction_type', '').strip(),
            'value': request.POST.get('value', '').strip(),
            'category_id': request.POST.get('category_id', '').strip(),
            'conta_id': request.POST.get('conta_id', '').strip(),
            'date': request.POST.get('date', '').strip(),  # <-- ADICIONE ESTA LINHA
        }
        errors, parsed_value, category, conta = validate_transaction_data(form_data, request.user, _get_categories_for_user)

        if not errors:
            extra_kwargs = {}
            if form_data['date']:
                extra_kwargs['date'] = form_data['date']
            Transaction.objects.create(
                user=request.user,
                name=form_data['name'],
                transaction_type=form_data['transaction_type'],
                value=parsed_value,
                category=category,
                conta=conta,
                **extra_kwargs 
            )
            return redirect('transactions:list')

        context = _build_create_transaction_context(request.user, form_data=form_data, errors=errors)
        return render(request, 'transactions/create_transaction.html', context)

    context = _build_create_transaction_context(request.user)
    return render(request, 'transactions/create_transaction.html', context)


# verificar e enviar os dados do form da transação para o banco de dados (ainda não implementado)
def post_transaction(request):
    return create_transactions(request)


# EXIBIR o extrato (entradas e saída) + o saldo
@login_required
def get_transactions(request):
    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month

    if month < 1:
        month, year = 12, year - 1
    elif month > 12:
        month, year = 1, year + 1

    # Cálculo do saldo total
    totais = Transaction.objects.filter(user=request.user).aggregate(
        e=Sum('value', filter=Q(transaction_type='DEPOSIT')),
        s=Sum('value', filter=Q(transaction_type='WITHDRAWAL'))
    )
    saldo = (totais['e'] or 0) - (totais['s'] or 0)

    # Transações por mês
    monthly_qs = Transaction.objects.filter(
        user=request.user, date__year=year, date__month=month
    ).order_by('-date', '-pk')

    monthly_totals = monthly_qs.aggregate(
        e=Sum('value', filter=Q(transaction_type='DEPOSIT')),
        s=Sum('value', filter=Q(transaction_type='WITHDRAWAL'))
    )
    balanco_mensal = (monthly_totals['e'] or 0) - (monthly_totals['s'] or 0)

    # Agrupamento por data
    groups = []
    yesterday = today - timedelta(days=1)
    for date_key, items in groupby(monthly_qs, key=lambda t: t.date):
        if date_key == today:
            label = f"Hoje, {date_key.day} de {date_fmt(date_key, 'F').lower()}"
        elif date_key == yesterday:
            label = f"Ontem, {date_key.day} de {date_fmt(date_key, 'F').lower()}"
        else:
            label = f"{date_key.day} de {date_fmt(date_key, 'F').lower()}"
        groups.append({'label': label, 'transactions': list(items)})

    # Navegação de meses
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render(request, 'transactions/list_transactions.html', {
        'groups': groups,
        'saldo': saldo,
        'balanco_mensal': balanco_mensal,
        'balanco_positivo': balanco_mensal >= 0,
        'month_name': date_fmt(date(year, month, 1), "F"),
        'year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    })

@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
 
    if request.method == 'POST':
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'transaction_type': request.POST.get('transaction_type', '').strip(),
            'value': request.POST.get('value', '').strip(),
            'category_id': request.POST.get('category_id', '').strip(),
            'conta_id': request.POST.get('conta_id', '').strip(),
            'date': request.POST.get('date', '').strip(),
        }
        errors, parsed_value, category, conta = validate_transaction_data(form_data, request.user, _get_categories_for_user)
 
        if not errors:
            transaction.name = form_data['name']
            transaction.transaction_type = form_data['transaction_type']
            transaction.value = parsed_value
            transaction.category = category
            transaction.conta = conta
            if form_data['date']:
                transaction.date = form_data['date']
            transaction.save()
            return redirect('transactions:list')
 
        context = _build_edit_transaction_context(request.user, transaction, form_data=form_data, errors=errors)
        return render(request, 'transactions/edit_transaction.html', context)
 
    form_data = {
        'name': transaction.name,
        'transaction_type': transaction.transaction_type,
        'value': str(transaction.value).replace('.', ','),
        'category_id': str(transaction.category.pk) if transaction.category else '',
        'conta_id': str(transaction.conta.pk) if transaction.conta else '',
        'date': transaction.date.strftime('%Y-%m-%d') if transaction.date else '',
    }
    context = _build_edit_transaction_context(request.user, transaction, form_data=form_data)
    return render(request, 'transactions/edit_transaction.html', context)
 
 
def _build_edit_transaction_context(user, transaction, form_data=None, errors=None):
    from django.db.models import Sum, Q
    totais = Transaction.objects.filter(user=user).aggregate(
        e=Sum('value', filter=Q(transaction_type='DEPOSIT')),
        s=Sum('value', filter=Q(transaction_type='WITHDRAWAL'))
    )
    account_balance = (totais['e'] or 0) - (totais['s'] or 0)
    contas = Conta.objects.filter(usuario=user)
    return {
        'transaction': transaction,
        'form_data': form_data or {},
        'errors': errors or {},
        'account_balance': account_balance,
        'transaction_type_choices': Transaction.TYPE_CHOICES,
        'categories': _get_categories_for_user(user),
        'contas': contas,
    }
 
 
@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
 
    if request.method == 'POST':
        transaction.delete()
        return redirect('transactions:list')
 
    return render(request, 'transactions/delete_transaction.html', {'transaction': transaction})
 