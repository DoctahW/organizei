from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subscription
from apps.transactions.models import Transaction, Category


def _get_subscription_category():
    return Category.objects.filter(
        user=None, name=Category.SUBSCRIPTION_CATEGORY_NAME
    ).first()


def _generate_subscription_occurrences(subscription):
    base_date = subscription.start_date
    occurrences = []
    for i in range(12):
        target = base_date + relativedelta(months=i)
        try:
            vencimento = date(target.year, target.month, base_date.day)
        except ValueError:
            next_month = date(target.year, target.month, 1) + relativedelta(months=1)
            vencimento = next_month - relativedelta(days=1)

        if vencimento < base_date:
            continue
        if subscription.end_date and vencimento > subscription.end_date:
            break

        occurrences.append(vencimento)
    return occurrences


def _create_transactions_for_subscription(subscription, user):
    category = _get_subscription_category()
    occurrences = _generate_subscription_occurrences(subscription)

    transactions = [
        Transaction(
            user=user,
            name=subscription.name,
            transaction_type='WITHDRAWAL',
            value=subscription.value,
            category=category,
            subscription=subscription,
            date=vencimento,
            is_fixed=True,
        )
        for vencimento in occurrences
    ]
    Transaction.objects.bulk_create(transactions)


@login_required
def manage_subscriptions(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        value = request.POST.get('value').replace('R$', '').replace('.', '').replace(',', '.').strip()
        start_date_raw = request.POST.get('start_date')
        end_date_raw = request.POST.get('end_date') or None

        start_date_input = (
            datetime.strptime(start_date_raw, '%Y-%m-%d').date()
            if start_date_raw else date.today()
        )
        end_date_input = (
            datetime.strptime(end_date_raw, '%Y-%m-%d').date()
            if end_date_raw else None
        )

        subscription = Subscription.objects.create(
            user=request.user,
            name=name,
            value=value,
            start_date=start_date_input,
            end_date=end_date_input,
        )

        _create_transactions_for_subscription(subscription, request.user)

        return redirect('subscriptions:manage_subscriptions')

    from django.db.models import Count
    subs = Subscription.objects.filter(user=request.user).prefetch_related('transactions')
    today = date.today()

    for sub in subs:
        sub.remaining_months = sub.transactions.filter(date__gte=today).count()

    from django.db.models import Sum as DSum
    from apps.transactions.models import Transaction as Tx

    totals = Tx.objects.filter(
        subscription__in=subs,
        user=request.user,
    ).aggregate(
        total_geral=DSum('value'),
        total_pago=DSum('value', filter=Q(date__lte=today)),
        total_a_pagar=DSum('value', filter=Q(date__gt=today)),
    )

    context = {
        'subscriptions': subs,
        'total_geral': totals['total_geral'] or 0,
        'total_pago': totals['total_pago'] or 0,
        'total_a_pagar': totals['total_a_pagar'] or 0,
        'hoje': today,
    }
    return render(request, 'subscriptions/manage_subscriptions.html', context)


@login_required
def subscription_detail(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    today = date.today()

    transactions = Transaction.objects.filter(
        subscription=subscription,
        user=request.user,
    ).order_by('date')

    occurrences = [
        {
            'vencimento': tx.date,
            'value': tx.value,
            'is_pago': tx.date <= today,
        }
        for tx in transactions
    ]

    context = {
        'subscription': subscription,
        'occurrences': occurrences,
    }
    return render(request, 'subscriptions/subscription_detail.html', context)


@login_required
def delete_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == 'POST':
        subscription.delete()
    return redirect('subscriptions:manage_subscriptions')