from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subscription
from apps.transactions.models import Transaction 
from datetime import date
from django.db.models import Sum

@login_required
def manage_subscriptions(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        value = request.POST.get('value').replace('R$', '').replace('.', '').replace(',', '.').strip()
        day = request.POST.get('day')
        Subscription.objects.create(user=request.user, name=name, value=value, day_of_month=day)
        return redirect('subscriptions:manage_subscriptions')

    subs = Subscription.objects.filter(user=request.user)
    today = date.today()

    total_geral = subs.aggregate(Sum('value'))['value__sum'] or 0
    total_pago = subs.filter(day_of_month__lte=today.day).aggregate(Sum('value'))['value__sum'] or 0
    
    total_a_pagar = subs.filter(day_of_month__gt=today.day).aggregate(Sum('value'))['value__sum'] or 0

    context = {
        'subscriptions': subs,
        'total_geral': total_geral,
        'total_pago': total_pago,
        'total_a_pagar': total_a_pagar,
        'hoje': today,
    }

    return render(request, 'subscriptions/manage_subscriptions.html', context)

@login_required
def delete_subscription(request, pk):
    sub = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == 'POST':
        sub.delete()
    return redirect('subscriptions:manage_subscriptions')