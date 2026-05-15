from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subscription
from apps.transactions.models import Transaction 
from datetime import date

@login_required
def manage_subscriptions(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        value = request.POST.get('value').replace('R$', '').replace('.', '').replace(',', '.').strip()
        day = request.POST.get('day')
        
        Subscription.objects.create(
            user=request.user,
            name=name,
            value=value,
            day_of_month=day
        )
        return redirect('subscriptions:manage_subscriptions')

    subs = Subscription.objects.filter(user=request.user)
    return render(request, 'subscriptions/manage_subscriptions.html', {'subscriptions': subs})

@login_required
def delete_subscription(request, pk):
    sub = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == 'POST':
        sub.delete()
    return redirect('subscriptions:manage_subscriptions')