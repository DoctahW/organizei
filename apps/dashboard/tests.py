from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from apps.transactions.models import Transaction
from apps.bank_accounts.models import Conta, Bank
from apps.goals.models import Goal
from apps.budget.models import Budget
from apps.investments.models import Investment
from .services import build_dashboard_context, get_patrimonio_series


def make_transaction(user, value, transaction_type, days_ago=0, conta=None):
    t = Transaction.objects.create(
        user=user, name="tx", value=value, transaction_type=transaction_type, conta=conta
    )
    if days_ago:
        Transaction.objects.filter(pk=t.pk).update(
            date=date.today() - timedelta(days=days_ago)
        )
    return t


def make_goal(user, deadline_days=30, is_completed=False, target=Decimal("1000.00")):
    return Goal.objects.create(
        user=user,
        name="Meta",
        target_amount=target,
        deadline=date.today() + timedelta(days=deadline_days),
        is_completed=is_completed,
    )


def make_budget(user, limit):
    return Budget.objects.create(user=user, month=date.today().replace(day=1), limit=limit)


def make_investment(user, valor_atual=Decimal("500.00")):
    return Investment.objects.create(
        usuario=user,
        nome="Test Investment",
        tipo="acao",
        valor_atual=valor_atual,
    )


class DashboardServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.bank = Bank.objects.create(name="Test Bank")
        self.conta = Conta.objects.create(bank=self.bank, usuario=self.user, account_type="corrente", number="12345")

    def test_empty_user_returns_is_empty_true(self):
        ctx = build_dashboard_context(self.user)
        self.assertTrue(ctx["is_empty"])

    def test_balance_is_deposits_minus_withdrawals(self):
        make_transaction(self.user, Decimal("500.00"), "DEPOSIT", conta=self.conta)
        make_transaction(self.user, Decimal("200.00"), "WITHDRAWAL", conta=self.conta)
        ctx = build_dashboard_context(self.user)
        self.assertEqual(ctx["total_balance"], Decimal("300.00"))

    def test_month_aggregates_only_current_month(self):
        make_transaction(self.user, Decimal("1000.00"), "DEPOSIT", days_ago=40, conta=self.conta)
        make_transaction(self.user, Decimal("100.00"), "DEPOSIT", conta=self.conta)
        ctx = build_dashboard_context(self.user)
        self.assertEqual(ctx["month_summary"]["income"], Decimal("100.00"))

    def test_nearest_goal_picks_smallest_future_deadline(self):
        make_goal(self.user, deadline_days=60)
        closer = make_goal(self.user, deadline_days=10)
        ctx = build_dashboard_context(self.user)
        self.assertEqual(ctx["priority_goal"].pk, closer.pk)

    def test_budget_level_warning_at_80_percent_boundary(self):
        make_budget(self.user, Decimal("100.00"))
        make_transaction(self.user, Decimal("80.00"), "WITHDRAWAL", conta=self.conta)
        ctx = build_dashboard_context(self.user)
        self.assertEqual(ctx["budget_status"]["level"], "warning")

    def test_budget_level_exceeded_at_100_percent_boundary(self):
        make_budget(self.user, Decimal("100.00"))
        make_transaction(self.user, Decimal("100.00"), "WITHDRAWAL", conta=self.conta)
        ctx = build_dashboard_context(self.user)
        self.assertEqual(ctx["budget_status"]["level"], "exceeded")

    def test_budget_status_none_when_no_budget_for_month(self):
        ctx = build_dashboard_context(self.user)
        self.assertIsNone(ctx["budget_status"])

    def test_patrimonio_includes_investment_value(self):
        make_transaction(self.user, Decimal("100"), "DEPOSIT", conta=self.conta)
        make_investment(self.user, valor_atual=Decimal("500"))
        result = get_patrimonio_series(self.user, "1M")
        self.assertEqual(result["series"][-1]["value"], 600.0)
        self.assertEqual(result["current_value"], Decimal("600.00"))

    def test_is_empty_false_when_only_investments_exist(self):
        make_investment(self.user)
        ctx = build_dashboard_context(self.user)
        self.assertFalse(ctx["is_empty"])

    def test_patrimonio_change_percent_with_investments(self):
        make_transaction(self.user, Decimal("100"), "DEPOSIT", days_ago=30, conta=self.conta)
        make_investment(self.user, valor_atual=Decimal("200"))
        make_transaction(self.user, Decimal("50"), "DEPOSIT", conta=self.conta)
        result = get_patrimonio_series(self.user, "1M")
        self.assertEqual(result["series"][0]["value"], 300.0)
        self.assertEqual(result["series"][-1]["value"], 350.0)
        self.assertEqual(result["change_absolute"], Decimal("50.00"))
        self.assertEqual(result["change_percent"], Decimal("16.67"))

    def test_patrimonio_all_period_with_investments_no_transactions(self):
        """ALL period should work when user has investments but no transactions."""
        make_investment(self.user, valor_atual=Decimal("1412.50"))
        data = get_patrimonio_series(self.user, "ALL")
        self.assertEqual(data["current_value"], Decimal("1412.50"))
        self.assertEqual(len(data["series"]), 1)
        self.assertEqual(data["series"][0]["value"], 1412.50)
