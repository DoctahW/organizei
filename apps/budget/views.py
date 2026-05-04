from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Budget
from django.db.models import Sum
from datetime import date
from apps.transactions.models import Transaction

from .services import validate_budget_data

@login_required
def set_budget(request):
    errors = {}
    if request.method == 'POST':
        data = {"limit": request.POST.get('limit')}
        errors, limit = validate_budget_data(data)

        if not errors:
            today = date.today()
            month_start = date(today.year, today.month, 1)

            Budget.objects.update_or_create(
                user=request.user,
                month=month_start,
                defaults={'limit': limit}
            )

            return redirect('budget:list')

    return render(request, 'budget/set_budget.html', {'errors': errors})

@login_required
def budget_view(request):
    today = date.today()

    budget_obj = Budget.objects.filter(
        user=request.user,
        month__month=today.month,
        month__year=today.year
    ).first()

    total = Transaction.objects.filter(
        user=request.user,
        date__month=today.month,
        date__year=today.year,
        transaction_type='WITHDRAWAL'
    ).aggregate(total=Sum('value'))['total'] or 0

    percent = 0
    if budget_obj and budget_obj.limit > 0:
        percent = (total / budget_obj.limit) * 100

    return render(request, 'budget/budget.html', {
        'budget': budget_obj,
        'total': total,
        'percent': percent
    })