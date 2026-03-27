from django.contrib import admin

from .models import Goal, GoalContribution


class GoalContributionInline(admin.TabularInline):
    model = GoalContribution
    extra = 1


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ["name", "target_amount", "deadline", "progress_percent", "is_completed"]
    list_filter = ["is_completed"]
    inlines = [GoalContributionInline]


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    list_display = ["goal", "amount", "date"]
