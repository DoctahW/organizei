from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subscription
from apps.transactions.models import Transaction 
from datetime import date
from django.db.models import Sum
from dateutil.relativedelta import relativedelta

from datetime import date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Subscription

@login_required
def manage_subscriptions(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        value = request.POST.get('value').replace('R$', '').replace('.', '').replace(',', '.').strip()
        start_date_input = request.POST.get('start_date')
        end_date_input = request.POST.get('end_date') or None
        
        Subscription.objects.create(
            user=request.user, name=name, value=value, 
            start_date=start_date_input, end_date=end_date_input
        )
        return redirect('subscriptions:manage_subscriptions')

    subs = Subscription.objects.filter(user=request.user)
    today = date.today()
    total_geral_ano = 0
    total_pago_ano = 0
    total_a_pagar_ano = 0

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
            if sub.end_date and vencimento > sub.end_date:
                break
            total_geral_ano += val

            if vencimento <= today:
                total_pago_ano += val
            else:
                total_a_pagar_ano += val
    context = {
        'subscriptions': subs,  
        'total_geral': total_geral_ano,     
        'total_pago': total_pago_ano,       
        'total_a_pagar': total_a_pagar_ano,  
        'hoje': today,
    }
    return render(request, 'subscriptions/manage_subscriptions.html', context)

@login_required
def subscription_detail(request, pk):
    sub = get_object_or_404(Subscription, pk=pk, user=request.user)
    today = date.today()
    
    projected_occurrences = []
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
        if sub.end_date and vencimento > sub.end_date:
            break 

        projected_occurrences.append({
            'vencimento': vencimento,
            'is_pago': vencimento <= today
        })

    return render(request, 'subscriptions/subscription_detail.html', {
        'subscription': sub,
        'occurrences': projected_occurrences
    })

@login_required
def delete_subscription(request, pk):
    sub = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == 'POST':
        sub.delete()
    return redirect('subscriptions:manage_subscriptions')