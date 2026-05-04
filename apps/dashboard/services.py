import math
from calendar import monthrange
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.dateformat import format as date_fmt
from django.utils.timezone import localdate

BUDGET_WARNING_THRESHOLD = Decimal("80")
BUDGET_EXCEEDED_THRESHOLD = Decimal("100")

# Funções helpers (_ no incio) são para não se repetir demais no bruto do codigo
def _prev_month(d: date) -> date:
    if d.month == 1:
        return date(d.year - 1, 12, 1)
    return date(d.year, d.month - 1, 1)

def _empty_patrimonio(period: str) -> dict:
    return {
        "period": period,
        "current_value": Decimal("0"),
        "change_absolute": Decimal("0"),
        "change_percent": Decimal("0"),
        "series": [],
    }
    
def _month_name(d: date) -> str:
    return date_fmt(d, "F/Y")

def _today_display(d: date) -> str:
    weekday = date_fmt(d, "l")
    month = date_fmt(d, "F").lower()
    return f"{weekday}, {d.day} de {month}"

def _safe_change_percent(change: Decimal, base: Decimal) -> Decimal:
    """(change / |base|) * 100 or 0 if base is zero."""
    if not base:
        return Decimal("0.00")
    return (change / abs(base) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _last_n_months(today: date, n: int) -> list:
    months = []
    y, m = today.year, today.month
    for _ in range(n):
        months.insert(0, date(y, m, 1))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return months

def _months_range(start: date, end: date) -> list:
    months = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.append(date(y, m, 1))
        m += 1
        if m == 13:
            m = 1
            y += 1
    return months

def _budget_status_for(user, month: date, expense: Decimal):
    budget = user.budget_set.filter(
        month__year=month.year,
        month__month=month.month,
    ).first()
    if not budget:
        return None
    percent = (expense / budget.limit * 100) if budget.limit else Decimal("0")
    if percent >= BUDGET_EXCEEDED_THRESHOLD:
        level = "exceeded"
    elif percent >= BUDGET_WARNING_THRESHOLD:
        level = "warning"
    else:
        level = "ok"
    remaining = max(Decimal("0"), budget.limit - expense)
    exceeded_by = max(Decimal("0"), expense - budget.limit)
    return {
        "limit": budget.limit,
        "spent": expense,
        "percent": round(percent, 1),
        "level": level,
        "remaining": remaining,
        "exceeded_by": exceeded_by,
    }

def _enrich_priority_goal(goal, today: date) -> None:
    current_amount = getattr(goal, "cached_amount", goal.current_amount)
    days_remaining = (goal.deadline - today).days
    months_remaining = max(1, math.ceil(days_remaining / 30))
    remaining = max(Decimal("0"), goal.target_amount - current_amount)
    if goal.target_amount:
        monthly_contribution_needed = (remaining / months_remaining).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        monthly_contribution_needed = Decimal("0.00")
    goal.days_remaining = days_remaining
    goal.monthly_contribution_needed = monthly_contribution_needed

def get_patrimonio_series(user, period: str) -> dict:
    # formula que cria as séries de patrimônio para o gráfico de evolução que nem sei se vai ser possivel de fazer mas a logica ta aqui
    today = localdate()
    transactions = user.transaction_set.all()

    if period == "1M":
        start_date = today - timedelta(days=29)

        initial_balance = transactions.filter(date__lt=start_date).aggregate(
            total=Coalesce(
                Sum("value", filter=Q(transaction_type="DEPOSIT")), Decimal("0")
            ) - Coalesce(
                Sum("value", filter=Q(transaction_type="WITHDRAWAL")), Decimal("0")
            )
        )["total"] or Decimal("0")

        daily_nets: dict = {}
        for tx in transactions.filter(
            date__gte=start_date, date__lte=today
        ).values("date", "transaction_type", "value"):
            delta = tx["value"] if tx["transaction_type"] == "DEPOSIT" else -tx["value"]
            daily_nets[tx["date"]] = daily_nets.get(tx["date"], Decimal("0")) + delta

        series = []
        running = initial_balance
        d = start_date
        while d <= today:
            running += daily_nets.get(d, Decimal("0"))
            series.append({"date": d.strftime("%d/%m"), "value": float(running)})
            d += timedelta(days=1)

    else:
        if period == "6M":
            months = _last_n_months(today, 6)
        elif period == "1A":
            months = _last_n_months(today, 12)
        else: 
            first_tx = transactions.order_by("date").first()
            if not first_tx:
                return _empty_patrimonio(period)
            months = _months_range(date(first_tx.date.year, first_tx.date.month, 1), today)

        if not months:
            return _empty_patrimonio(period)

        start_date = months[0]
        last_month = months[-1]
        last_day = date(
            last_month.year,
            last_month.month,
            monthrange(last_month.year, last_month.month)[1],
        )

        initial_balance = transactions.filter(date__lt=start_date).aggregate(
            total=Coalesce(
                Sum("value", filter=Q(transaction_type="DEPOSIT")), Decimal("0")
            ) - Coalesce(
                Sum("value", filter=Q(transaction_type="WITHDRAWAL")), Decimal("0")
            )
        )["total"] or Decimal("0")

        monthly_nets: dict = {}
        for tx in transactions.filter(
            date__gte=start_date, date__lte=last_day
        ).values("date", "transaction_type", "value"):
            key = (tx["date"].year, tx["date"].month)
            delta = tx["value"] if tx["transaction_type"] == "DEPOSIT" else -tx["value"]
            monthly_nets[key] = monthly_nets.get(key, Decimal("0")) + delta

        series = []
        running = initial_balance
        for month_start in months:
            key = (month_start.year, month_start.month)
            running += monthly_nets.get(key, Decimal("0"))
            series.append({"date": month_start.strftime("%m/%y"), "value": float(running)})

    if not series:
        return _empty_patrimonio(period)

    current_value = Decimal(str(series[-1]["value"]))
    first_value = Decimal(str(series[0]["value"]))
    change_absolute = current_value - first_value
    change_percent = _safe_change_percent(change_absolute, first_value)

    return {
        "period": period,
        "current_value": current_value.quantize(Decimal("0.01")),
        "change_absolute": change_absolute.quantize(Decimal("0.01")),
        "change_percent": change_percent,
        "series": series,
    }
    
def get_movimentacao_by_month(user, month: date) -> dict:
    transactions = user.transaction_set.all()

    income = transactions.filter(
        transaction_type="DEPOSIT",
        date__year=month.year,
        date__month=month.month,
    ).aggregate(total=Coalesce(Sum("value"), Decimal("0")))["total"]

    expense = transactions.filter(
        transaction_type="WITHDRAWAL",
        date__year=month.year,
        date__month=month.month,
    ).aggregate(total=Coalesce(Sum("value"), Decimal("0")))["total"]

    balance = income - expense

    prev = _prev_month(month)
    prev_income = transactions.filter(
        transaction_type="DEPOSIT",
        date__year=prev.year,
        date__month=prev.month,
    ).aggregate(total=Coalesce(Sum("value"), Decimal("0")))["total"]
    prev_expense = transactions.filter(
        transaction_type="WITHDRAWAL",
        date__year=prev.year,
        date__month=prev.month,
    ).aggregate(total=Coalesce(Sum("value"), Decimal("0")))["total"]
    prev_balance = prev_income - prev_expense

    balance_change_percent = _safe_change_percent(balance - prev_balance, prev_balance)

    budget_status = _budget_status_for(user, month, expense)

    total = income + expense
    if total:
        income_bar = f"{float(income / total * 100):.1f}"
        expense_bar = f"{float(expense / total * 100):.1f}"
    else:
        income_bar = expense_bar = "0.0"

    return {
        "reference_month": _month_name(month),
        "month_short": date_fmt(month, "F"),
        "income": income,
        "expense": expense,
        "balance": balance,
        "prev_month_balance": prev_balance,
        "balance_change_percent": balance_change_percent,
        "income_bar_percent": income_bar,
        "expense_bar_percent": expense_bar,
        "budget_status": budget_status,
    }
    
def get_top_categories(user, month: date) -> list:
    current_qs = (
        user.transaction_set.filter(
            transaction_type="WITHDRAWAL",
            date__year=month.year,
            date__month=month.month,
        )
        .values("category__id", "category__name")
        .annotate(total=Sum("value"))
        .order_by("-total")
    )

    prev = _prev_month(month)
    prev_map: dict = {
        row["category__id"]: row["total"]
        for row in user.transaction_set.filter(
            transaction_type="WITHDRAWAL",
            date__year=prev.year,
            date__month=prev.month,
        )
        .values("category__id")
        .annotate(total=Sum("value"))
    }

    categories = []
    for row in current_qs:
        cat_id = row["category__id"]
        name = row["category__name"] or "Outros"
        current = row["total"]
        prev_amount = prev_map.get(cat_id, Decimal("0"))

        change_percent = _safe_change_percent(current - prev_amount, prev_amount)
        max_val = max(current, prev_amount)
        bar_percent = (current / max_val * 100).quantize(Decimal("0.1")) if max_val else Decimal("0")
        bar_percent = min(bar_percent, Decimal("100"))

        categories.append({
            "name": name,
            "icon": "",   #TODO: Ainda não tem icone, mudança futura importante
            "color": "",  #TODO: Ainda não tem cor, mudança futura importante
            "current_amount": current,
            "prev_amount": prev_amount,
            "change_percent": change_percent,
            "bar_percent": bar_percent,
        })

    return categories[:7]

def build_dashboard_context(user) -> dict:
    # construtor principal da dashboard
    today = localdate()
    transactions = user.transaction_set.all()
    total_balance = transactions.aggregate(
        total=Coalesce(
            Sum("value", filter=Q(transaction_type="DEPOSIT")), Decimal("0")
        ) - Coalesce(
            Sum("value", filter=Q(transaction_type="WITHDRAWAL")), Decimal("0")
        )
    )["total"]

    month_data = get_movimentacao_by_month(user, today)
    month_summary = {
        "reference_month": month_data["reference_month"],
        "month_short": month_data["month_short"],
        "income": month_data["income"],
        "expense": month_data["expense"],
        "balance": month_data["balance"],
        "prev_month_balance": month_data["prev_month_balance"],
        "balance_change_percent": month_data["balance_change_percent"],
        "income_bar_percent": month_data["income_bar_percent"],
        "expense_bar_percent": month_data["expense_bar_percent"],
    }
    budget_status = month_data["budget_status"]

    top_categories = get_top_categories(user, today)
    
    #seção de objetivos na dashboard
    all_incomplete = list(
        user.goals.filter(is_completed=False)
        .annotate(current_amount=Coalesce(Sum("contributions__amount"), Value(Decimal("0.00"))))
        .order_by("deadline")
    )

    # logica pra reduzir numero de queries
    for goal in all_incomplete:
        goal.cached_amount = goal.current_amount
        goal.cached_progress = (
            min(float(goal.cached_amount / goal.target_amount * 100), 100.0)
            if goal.target_amount
            else 0.0
        )

    future_goals = [g for g in all_incomplete if g.deadline >= today]
    if future_goals:
        priority_goal = future_goals[0]
    elif all_incomplete:
        priority_goal = max(all_incomplete, key=lambda g: g.created_at)
    else:
        priority_goal = None

    if priority_goal:
        _enrich_priority_goal(priority_goal, today)

    other_goals = [g for g in all_incomplete if g is not priority_goal][:3]

    # se Deus perimitir vou conseguir o chart.js com essa aqui
    patrimonio_initial = get_patrimonio_series(user, "1M")
    
    is_empty = (
        not transactions.exists()
        and not user.goals.exists()
        and budget_status is None
    )

    return {
        "user_first_name": user.first_name or user.username,
        "today": today,
        "today_display": _today_display(today),
        "total_balance": total_balance,
        "month_summary": month_summary,
        "budget_status": budget_status,
        "top_categories": top_categories,
        "priority_goal": priority_goal,
        "other_goals": other_goals,
        "patrimonio_initial": patrimonio_initial,
        "is_empty": is_empty,
    }
