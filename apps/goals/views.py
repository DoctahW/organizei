from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from .models import Goal, GoalContribution
from .services import validate_goal_data, validate_contribution_data


@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user).annotate(
        current_amount=Coalesce(Sum("contributions__amount"), Value(Decimal("0.00")))
    )

    total_target = goals.aggregate(total=Sum("target_amount"))["total"] or 0
    total_saved = sum(g.current_amount for g in goals)

    context = {
        "goals": goals,
        "total_target": total_target,
        "total_saved": total_saved,
    }
    return render(request, "goals/list.html", context)


@login_required
def goal_create(request):
    errors = {}
    data = {}

    if request.method == "POST":
        data = {
            "name": request.POST.get("name", "").strip(),
            "target_amount": request.POST.get("target_amount", "").strip(),
            "deadline": request.POST.get("deadline", "").strip(),
        }

        errors, amount = validate_goal_data(data)

        if not errors:
            goal = Goal.objects.create(
                user=request.user,
                name=data["name"],
                target_amount=amount,
                deadline=data["deadline"],
            )
            messages.success(request, f'Meta "{goal.name}" criada com sucesso!')
            return redirect("goals:list")

    return render(request, "goals/form.html", {"errors": errors, "data": data})


@login_required
def goal_detail(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    contributions = goal.contributions.all()
    return render(request, "goals/detail.html", {"goal": goal, "contributions": contributions})


@login_required
def goal_contribute(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    errors = {}
    data = {}

    if request.method == "POST":
        data = {
            "amount": request.POST.get("amount", "").strip(),
            "date": request.POST.get("date", "").strip(),
        }

        errors, amount = validate_contribution_data(data)

        if not errors:
            contribution = GoalContribution.objects.create(
                goal=goal,
                amount=amount,
                date=data["date"],
            )
            just_completed = goal.check_completion()
            if just_completed:
                messages.success(request, f'Parabéns! Você atingiu sua meta "{goal.name}"! 🎉')
            else:
                messages.success(request, f"Contribuição de R$ {contribution.amount} registrada!")
            return redirect("goals:detail", pk=pk)

    return render(request, "goals/contribute.html", {"errors": errors, "data": data, "goal": goal})
