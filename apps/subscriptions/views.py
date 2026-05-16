from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required  # <--- ESSA LINHA AQUI
from .models import Subscription

@login_required
def manage_subscriptions(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        value = request.POST.get('value').replace('R$', '').replace('.', '').replace(',', '.').strip()
        start_date_raw = request.POST.get('start_date')
        end_date_raw = request.POST.get('end_date') or None
        
        if start_date_raw:
            start_date_input = datetime.strptime(start_date_raw, '%Y-%m-%d').date()
        else:
            start_date_input = date.today()
            
        if end_date_raw:
            end_date_input = datetime.strptime(end_date_raw, '%Y-%m-%d').date()
        else:
            end_date_input = None
        
        Subscription.objects.create(
            user=request.user, 
            name=name, 
            value=value, 
            start_date=start_date_input, 
            end_date=end_date_input
        )
        return redirect('subscriptions:manage_subscriptions')

    subs = Subscription.objects.filter(user=request.user)
    today = date.today()
    total_geral_ano = 0
    total_pago_ano = 0
    total_a_pagar_ano = 0

    for sub in subs:
        val = float(sub.value)        
        base_date = sub.start_date if sub.start_date < today else today

        for i in range(12):
            target_month_date = base_date + relativedelta(months=i)
            try:
                vencimento = date(target_month_date.year, target_month_date.month, sub.start_date.day)
            except ValueError:
                next_month = date(target_month_date.year, target_month_date.month, 1) + relativedelta(months=1)
                vencimento = next_month - relativedelta(days=1)

            if vencimento < sub.start_date:
                continue
            if sub.end_date and vencimento > sub.end_date:
                continue

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


# === 2. VIEW DE DETALHES (Gera a lista física "occurrences" com os cards retroativos e futuros) ===
@login_required
def subscription_detail(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    today = date.today()
    
    occurrences = []
    # Começa estritamente no início do contrato para não sumir com o passado
    base_date = subscription.start_date

    # Calcula a janela dinâmica para exibir o passado inteiro + 12 meses futuros
    meses_passados = (today.year - base_date.year) * 12 + (today.month - base_date.month)
    total_meses_janela = max(12, meses_passados + 12)

    for i in range(total_meses_janela):
        target_month_date = base_date + relativedelta(months=i)
        
        try:
            vencimento = date(target_month_date.year, target_month_date.month, subscription.start_date.day)
        except ValueError:
            next_month = date(target_month_date.year, target_month_date.month, 1) + relativedelta(months=1)
            vencimento = next_month - relativedelta(days=1)

        if vencimento < subscription.start_date:
            continue
        if subscription.end_date and vencimento > subscription.end_date:
            break

        occurrences.append({
            'vencimento': vencimento,
            'is_pago': vencimento <= today
        })

    context = {
        'subscription': subscription,
        'occurrences': occurrences,
    }
    return render(request, 'subscriptions/subscription_detail.html', context)


# === 3. VIEW DE EXCLUSÃO (Caso você já tenha ela aí) ===
@login_required
def delete_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == 'POST':
        subscription.delete()
    return redirect('subscriptions:manage_subscriptions')