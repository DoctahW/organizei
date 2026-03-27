from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import GoalContributionForm, GoalForm
from .models import Goal


@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user).prefetch_related("contributions")

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
    if request.method == "POST":
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, f'Meta "{goal.name}" criada com sucesso!')
            return redirect("goals:list")
    else:
        form = GoalForm()
    return render(request, "goals/form.html", {"form": form})


@login_required
def goal_detail(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    contributions = goal.contributions.all()
    return render(request, "goals/detail.html", {"goal": goal, "contributions": contributions})


@login_required
def goal_contribute(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == "POST":
        form = GoalContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.goal = goal
            contribution.save()

            just_completed = goal.check_completion()
            if just_completed:
                messages.success(request, f'Parabéns! Você atingiu sua meta "{goal.name}"! 🎉')
            else:
                messages.success(request, f"Contribuição de R$ {contribution.amount} registrada!")

            return redirect("goals:detail", pk=pk)
    else:
        form = GoalContributionForm()
    return render(request, "goals/contribute.html", {"form": form, "goal": goal})
