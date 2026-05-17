from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from itertools import groupby

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.dateformat import format as date_fmt
from .models import Transaction, Category
from django.db.models import Sum, Q
from apps.bank_accounts.models import Conta
from .services import validate_transaction_data


def _get_categories_for_user(user):
    return Category.objects.filter(
        Q(user=None) | Q(user=user)
    ).exclude(
        user=None, name=Category.SUBSCRIPTION_CATEGORY_NAME
    ).order_by('name')


def _build_create_transaction_context(user, form_data=None, errors=None):
    totais = Transaction.objects.filter(user=user, date__lte=date.today()).aggregate(
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


@login_required
def create_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name and name.lower() != Category.SUBSCRIPTION_CATEGORY_NAME.lower():
            Category.objects.create(name=name, user=request.user)
        return redirect('transactions:create_transaction')
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
            'date': request.POST.get('date', '').strip(),
        }

        is_fixed_input = request.POST.get('is_fixed') == 'on'

        errors, parsed_value, category, conta = validate_transaction_data(
            form_data, request.user, _get_categories_for_user
        )

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
                is_fixed=is_fixed_input,
                **extra_kwargs
            )

            if is_fixed_input:
                start_date = datetime.strptime(form_data['date'], '%Y-%m-%d').date() if form_data['date'] else date.today()
                for i in range(1, 12):
                    Transaction.objects.create(
                        user=request.user,
                        name=form_data['name'],
                        transaction_type=form_data['transaction_type'],
                        value=parsed_value,
                        category=category,
                        conta=conta,
                        date=start_date + relativedelta(months=i),
                        is_fixed=True,
                    )

            return redirect('transactions:list')

        context = _build_create_transaction_context(request.user, form_data=form_data, errors=errors)
        return render(request, 'transactions/create_transaction.html', context)

    context = _build_create_transaction_context(request.user)
    return render(request, 'transactions/create_transaction.html', context)


def post_transaction(request):
    return create_transactions(request)


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

    totais = Transaction.objects.filter(user=request.user, date__lte=today).aggregate(
        e=Sum('value', filter=Q(transaction_type='DEPOSIT')),
        s=Sum('value', filter=Q(transaction_type='WITHDRAWAL'))
    )
    saldo = (totais['e'] or 0) - (totais['s'] or 0)

    monthly_qs = Transaction.objects.filter(
        user=request.user, date__year=year, date__month=month
    ).select_related('category').order_by('-date', '-id')

    monthly_totals = monthly_qs.aggregate(
        e=Sum('value', filter=Q(transaction_type='DEPOSIT')),
        s=Sum('value', filter=Q(transaction_type='WITHDRAWAL'))
    )
    balanco_mensal = (monthly_totals['e'] or 0) - (monthly_totals['s'] or 0)

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
        'hoje': today,
    })


@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    is_subscription = transaction.subscription_id is not None

    if request.method == 'POST':
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'transaction_type': request.POST.get('transaction_type', '').strip(),
            'value': request.POST.get('value', '').strip(),
            'category_id': (
                str(transaction.category.pk) if is_subscription and transaction.category
                else request.POST.get('category_id', '').strip()
            ),
            'conta_id': request.POST.get('conta_id', '').strip(),
            'date': request.POST.get('date', '').strip(),
            'is_fixed': request.POST.get('is_fixed', 'off'),
        }
        errors, parsed_value, category, conta = validate_transaction_data(
            form_data, request.user, _get_categories_for_user
        )

        if is_subscription:
            errors.pop('category_id', None)
            category = transaction.category

        if not errors:
            if is_subscription:
                subscription = transaction.subscription
                new_date = date.fromisoformat(form_data['date']) if form_data['date'] else transaction.date

                following = list(Transaction.objects.filter(
                    subscription=subscription,
                    date__gte=transaction.date,
                    user=request.user,
                ).order_by('date'))

                for i, tx in enumerate(following):
                    try:
                        tx.date = date(
                            (new_date + relativedelta(months=i)).year,
                            (new_date + relativedelta(months=i)).month,
                            new_date.day,
                        )
                    except ValueError:
                        next_month = date(
                            (new_date + relativedelta(months=i)).year,
                            (new_date + relativedelta(months=i)).month,
                            1,
                        ) + relativedelta(months=1)
                        tx.date = next_month - relativedelta(days=1)
                    tx.value = parsed_value
                    tx.conta = conta

                Transaction.objects.bulk_update(following, ['date', 'value', 'conta'])

                subscription.value = parsed_value
                subscription.start_date = following[0].date if following else new_date
                subscription.save()

            else:
                transaction.name = form_data['name']
                transaction.transaction_type = form_data['transaction_type']
                transaction.value = parsed_value
                transaction.category = category
                transaction.conta = conta
                if form_data['date']:
                    transaction.date = form_data['date']
                transaction.is_fixed = form_data['is_fixed'] == 'on'
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
        'is_fixed': 'on' if transaction.is_fixed else 'off',
    }
    context = _build_edit_transaction_context(request.user, transaction, form_data=form_data)
    return render(request, 'transactions/edit_transaction.html', context)


def _build_edit_transaction_context(user, transaction, form_data=None, errors=None):
    totais = Transaction.objects.filter(user=user, date__lte=date.today()).aggregate(
        e=Sum('value', filter=Q(transaction_type='DEPOSIT')),
        s=Sum('value', filter=Q(transaction_type='WITHDRAWAL'))
    )
    account_balance = (totais['e'] or 0) - (totais['s'] or 0)
    contas = Conta.objects.filter(usuario=user)

    categories = _get_categories_for_user(user)

    return {
        'transaction': transaction,
        'is_subscription_transaction': transaction.subscription_id is not None,
        'form_data': form_data or {},
        'errors': errors or {},
        'account_balance': account_balance,
        'transaction_type_choices': Transaction.TYPE_CHOICES,
        'categories': categories,
        'contas': contas,
    }


@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if transaction.subscription_id is not None:
        return redirect('transactions:update', pk=pk)

    if request.method == 'POST':
        if transaction.is_fixed:
            Transaction.objects.filter(
                user=request.user,
                name=transaction.name,
                transaction_type=transaction.transaction_type,
                is_fixed=True,
                date__gte=transaction.date,
            ).delete()
        else:
            transaction.delete()
        return redirect('transactions:list')

    return render(request, 'transactions/delete_transaction.html', {'transaction': transaction})