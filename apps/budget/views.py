from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Budget
from django.db.models import Sum, Q
from datetime import date
from apps.transactions.models import Transaction, Category

from .services import validate_budget_data

@login_required
def set_budget(request):
    errors = {}
    categories = Category.objects.filter(Q(user=request.user) | Q(user__isnull=True)).exclude(name__icontains='salário')

    if request.method == 'POST':
        data = {"limit": request.POST.get('limit')}
        errors, limit = validate_budget_data(data)
        
        category_id = request.POST.get('category')
        if not category_id:
            errors['category'] = 'Selecione uma categoria.'

        if not errors:
            today = date.today()
            month_start = date(today.year, today.month, 1)
            category_obj = Category.objects.get(id=category_id)

            Budget.objects.update_or_create(
                user=request.user,
                month=month_start,
                category=category_obj,
                defaults={'limit': limit}
            )

            return redirect('budget:list')

    return render(request, 'budget/set_budget.html', {'errors': errors, 'categories': categories})

@login_required
def budget_view(request):
    today = date.today()

    budgets = Budget.objects.filter(
        user=request.user,
        month__month=today.month,
        month__year=today.year
    )

    for budget_obj in budgets:
        total = Transaction.objects.filter(
            user=request.user,
            category=budget_obj.category,
            date__month=today.month,
            date__year=today.year,
            transaction_type='WITHDRAWAL'
        ).aggregate(total=Sum('value'))['total'] or 0

        percent = 0
        if budget_obj.limit > 0:
            percent = (total / budget_obj.limit) * 100

        budget_obj.total = total
        budget_obj.percent = percent

    return render(request, 'budget/budget.html', {
        'budgets': budgets
    })