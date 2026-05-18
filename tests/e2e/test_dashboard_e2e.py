from datetime import date, timedelta

from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from apps.budget.models import Budget
from apps.goals.models import Goal
from apps.transactions.models import Category
from apps.transactions.models import Transaction
from apps.bank_accounts.models import Conta, Bank


from .base import E2EBaseTest


@tag("e2e")
class DashboardE2ETest(E2EBaseTest):
    def setUp(self):
        self.user = self.create_user()
        self.login_via_ui()
        self.bank = Bank.objects.create(name="Test Bank")
        self.conta = Conta.objects.create(bank=self.bank, usuario=self.user, account_type="corrente", number="12345")

    def test_empty_dashboard_shows_ctas(self):
        """A user with no data sees the empty-state CTA on the dashboard."""
        self.goto("dashboard:home")

        self.wait().until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-empty"))
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Nova Transação", body_text)

    def test_dashboard_shows_balance_and_nearest_goal(self):
        """Dashboard shows the user's total balance and priority goal name."""
        Transaction.objects.create(
            user=self.user,
            name="Salário",
            value=3000,
            transaction_type="DEPOSIT",
            date=date.today(),
            conta=self.conta,
        )
        Goal.objects.create(
            user=self.user,
            name="Reserva de emergência",
            target_amount=10000,
            deadline=date.today() + timedelta(days=365),
        )

        self.goto("dashboard:home")

        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("3000", body_text)
        self.assertIn("Reserva de emergência", body_text)

    def test_budget_card_turns_red_when_exceeded(self):
        """When spending exceeds the monthly budget the dashboard movimentação card
        shows the exceeded alert."""
        today = date.today()

        # Criando a categoria necessária para o banco de testes
        category = Category.objects.create(name="Alimentação", user=self.user)

        Budget.objects.create(
            user=self.user,
            month=date(today.year, today.month, 1),
            limit=500,
            category=category,
        )
        Transaction.objects.create(
            user=self.user,
            name="Gasto alto",
            value=600,
            transaction_type="WITHDRAWAL",
            date=today,
            conta=self.conta,
            category=category,
        )

        self.goto("dashboard:home")

        self.wait().until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".mov-budget-pct-exceeded")
            )
        )
        exceeded_el = self.driver.find_element(
            By.CSS_SELECTOR, ".mov-budget-pct-exceeded"
        )
        self.assertTrue(exceeded_el.is_displayed())
