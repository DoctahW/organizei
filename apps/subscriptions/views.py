from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subscription
from apps.transactions.models import Transaction 
from datetime import date
from django.db.models import Sum
from dateutil.relativedelta import relativedelta

@login_required
def manage_subscriptions(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        value = request.POST.get('value').replace('R$', '').replace('.', '').replace(',', '.').strip()
        start_date_input = request.POST.get('start_date') 
        
        Subscription.objects.create(
            user=request.user, 
            name=name, 
            value=value, 
            start_date=start_date_input
        )
        return redirect('subscriptions:manage_subscriptions')

    subs = Subscription.objects.filter(user=request.user)
    today = date.today()
    total_geral_ano = 0
    total_pago_ano = 0
    total_a_pagar_ano = 0   
    projected_occurrences = []

    for sub in subs:
        val = float(sub.value)        
        for i in range(12):
            target_month_date = today + relativedelta(months=i)            
            try:
                vencimento = date(target_month_date.year, target_month_date.month, sub.start_date.day)
            except ValueError:
                next_month = date(target_month_date.year, target_month_date.month, 1) + relativedelta(months=1)
                vencimento = next_month - relativedelta(days=1)
            if vencimento < sub.start_date:
                continue
            total_geral_ano += val

            if vencimento <= today:
                total_pago_ano += val
                status_pago = True
            else:
                total_a_pagar_ano += val
                status_pago = False
            projected_occurrences.append({
                'id': sub.id,
                'name': sub.name,
                'value': sub.value,
                'vencimento': vencimento,
                'is_pago': status_pago,
                'pk': sub.pk  
            })
    projected_occurrences = sorted(projected_occurrences, key=lambda x: x['vencimento'])

    context = {
        'subscriptions': projected_occurrences,
        'total_geral': total_geral_ano,
        'total_pago': total_pago_ano,
        'total_a_pagar': total_a_pagar_ano,
        'hoje': today,
    }
    return render(request, 'subscriptions/manage_subscriptions.html', context)

@login_required
def delete_subscription(request, pk):
    sub = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == 'POST':
        sub.delete()
    return redirect('subscriptions:manage_subscriptions')