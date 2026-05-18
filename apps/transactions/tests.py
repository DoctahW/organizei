from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Transaction, Category
from apps.bank_accounts.models import Conta, Bank

_TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.bank = Bank.objects.create(name="Test Bank")
        self.conta = Conta.objects.create(bank=self.bank, usuario=self.user, account_type="corrente", number="12345")

    def test_str_deposit(self):
        t = Transaction(user=self.user, name="Salário", value=Decimal("1000.00"), transaction_type="DEPOSIT", conta=self.conta)
        self.assertEqual(str(t), "Salário - R$ 1000.00 (Entrada)")

    def test_str_withdrawal(self):
        t = Transaction(user=self.user, name="Aluguel", value=Decimal("500.00"), transaction_type="WITHDRAWAL", conta=self.conta)
        self.assertEqual(str(t), "Aluguel - R$ 500.00 (Saída)")

    def test_date_auto_set_on_create(self):
        t = Transaction.objects.create(
            user=self.user, name="Teste", value=Decimal("10.00"), transaction_type="DEPOSIT", conta=self.conta
        )
        self.assertLessEqual(abs((t.date - timezone.now()).total_seconds()), 1)

    def test_cascade_delete_with_user(self):
        Transaction.objects.create(
            user=self.user, name="Teste", value=Decimal("10.00"), transaction_type="DEPOSIT", conta=self.conta
        )
        # PROTECT on conta prevents direct user delete while transactions exist
        from django.db.models import ProtectedError
        with self.assertRaises(ProtectedError):
            self.user.delete()
        # Must delete transactions first, then user
        Transaction.objects.all().delete()
        self.user.delete()
        self.assertEqual(Transaction.objects.count(), 0)


@override_settings(STORAGES=_TEST_STORAGES)
class CreateTransactionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.category = Category.objects.create(user=None, name="Outros")
        self.bank = Bank.objects.create(name="Test Bank")
        self.conta = Conta.objects.create(bank=self.bank, usuario=self.user, account_type="corrente", number="12345")
        self.url = reverse("transactions:create_transaction")

    def test_get_redirects_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_get_renders_form_authenticated(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("account_balance", response.context)
        self.assertIn("transaction_type_choices", response.context)
        self.assertIn("categories", response.context)

    def test_get_balance_is_zero_with_no_transactions(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.context["account_balance"], 0)

    def test_get_categories_includes_global(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        category_ids = [c.pk for c in response.context["categories"]]
        self.assertIn(self.category.pk, category_ids)

    def test_get_categories_includes_user_category(self):
        user_cat = Category.objects.create(user=self.user, name="Minha Categoria")
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        category_ids = [c.pk for c in response.context["categories"]]
        self.assertIn(user_cat.pk, category_ids)

    def test_get_categories_excludes_other_user_category(self):
        other_user = User.objects.create_user(username="other", password="pass")
        other_cat = Category.objects.create(user=other_user, name="Categoria Alheia")
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        category_ids = [c.pk for c in response.context["categories"]]
        self.assertNotIn(other_cat.pk, category_ids)

    def test_post_valid_deposit_creates_transaction(self):
        self.client.login(username="testuser", password="pass")
        self.client.post(self.url, {"name": "Salário", "transaction_type": "DEPOSIT", "value": "1000.00", "category_id": self.category.pk, "conta_id": self.conta.pk})
        self.assertEqual(Transaction.objects.count(), 1)
        t = Transaction.objects.first()
        self.assertEqual(t.transaction_type, "DEPOSIT")
        self.assertEqual(t.value, Decimal("1000.00"))
        self.assertEqual(t.category, self.category)

    def test_post_valid_withdrawal_creates_transaction(self):
        self.client.login(username="testuser", password="pass")
        self.client.post(self.url, {"name": "Aluguel", "transaction_type": "WITHDRAWAL", "value": "500.00", "category_id": self.category.pk, "conta_id": self.conta.pk})
        self.assertEqual(Transaction.objects.count(), 1)

    def test_post_valid_redirects_to_list(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            self.url, {"name": "Salário", "transaction_type": "DEPOSIT", "value": "1000.00", "category_id": self.category.pk, "conta_id": self.conta.pk}
        )
        self.assertRedirects(response, reverse("transactions:list"))

    def test_post_without_category_creates_transaction(self):
        self.client.login(username="testuser", password="pass")
        self.client.post(self.url, {"name": "Salário", "transaction_type": "DEPOSIT", "value": "1000.00", "conta_id": self.conta.pk})
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertIsNone(Transaction.objects.first().category)

    def test_post_comma_as_decimal_separator(self):
        self.client.login(username="testuser", password="pass")
        self.client.post(self.url, {"name": "Salário", "transaction_type": "DEPOSIT", "value": "1500,50", "category_id": self.category.pk, "conta_id": self.conta.pk})
        t = Transaction.objects.first()
        self.assertEqual(t.value, Decimal("1500.50"))

    def test_post_missing_name_shows_error(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(self.url, {"name": "", "transaction_type": "DEPOSIT", "value": "100.00", "category_id": self.category.pk, "conta_id": self.conta.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.context["errors"])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_post_name_too_long_shows_error(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            self.url, {"name": "a" * 151, "transaction_type": "DEPOSIT", "value": "100.00", "category_id": self.category.pk, "conta_id": self.conta.pk}
        )
        self.assertIn("name", response.context["errors"])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_post_invalid_transaction_type_shows_error(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(self.url, {"name": "Teste", "transaction_type": "INVALID", "value": "100.00", "category_id": self.category.pk, "conta_id": self.conta.pk})
        self.assertIn("transaction_type", response.context["errors"])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_post_invalid_category_shows_error(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(self.url, {"name": "Teste", "transaction_type": "DEPOSIT", "value": "100.00", "category_id": 99999, "conta_id": self.conta.pk})
        self.assertIn("category_id", response.context["errors"])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_post_category_of_other_user_shows_error(self):
        other_user = User.objects.create_user(username="other", password="pass")
        other_cat = Category.objects.create(user=other_user, name="Categoria Alheia")
        self.client.login(username="testuser", password="pass")
        response = self.client.post(self.url, {"name": "Teste", "transaction_type": "DEPOSIT", "value": "100.00", "category_id": other_cat.pk, "conta_id": self.conta.pk})
        self.assertIn("category_id", response.context["errors"])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_post_zero_value_shows_error(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(self.url, {"name": "Teste", "transaction_type": "DEPOSIT", "value": "0", "category_id": self.category.pk, "conta_id": self.conta.pk})
        self.assertIn("value", response.context["errors"])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_post_negative_value_shows_error(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(self.url, {"name": "Teste", "transaction_type": "DEPOSIT", "value": "-50", "category_id": self.category.pk, "conta_id": self.conta.pk})
        self.assertIn("value", response.context["errors"])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_post_non_numeric_value_shows_error(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(self.url, {"name": "Teste", "transaction_type": "DEPOSIT", "value": "abc", "category_id": self.category.pk, "conta_id": self.conta.pk})
        self.assertIn("value", response.context["errors"])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_post_preserves_form_data_on_error(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.post(self.url, {"name": "Teste", "transaction_type": "DEPOSIT", "value": "abc", "category_id": self.category.pk, "conta_id": self.conta.pk})
        self.assertEqual(response.context["form_data"]["name"], "Teste")

    def test_account_balance_reflects_existing_transactions(self):
        Transaction.objects.create(user=self.user, name="Entrada", value=Decimal("200.00"), transaction_type="DEPOSIT", conta=self.conta)
        Transaction.objects.create(user=self.user, name="Saída", value=Decimal("50.00"), transaction_type="WITHDRAWAL", conta=self.conta)
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.context["account_balance"], Decimal("150.00"))


@override_settings(STORAGES=_TEST_STORAGES)
class GetTransactionsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.bank = Bank.objects.create(name="Test Bank")
        self.conta = Conta.objects.create(bank=self.bank, usuario=self.user, account_type="corrente", number="12345")
        self.url = reverse("transactions:list")

    def test_redirects_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_renders_for_authenticated_user(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_only_shows_own_transactions(self):
        Transaction.objects.create(user=self.user, name="Minha", value=Decimal("100"), transaction_type="DEPOSIT", conta=self.conta)
        Transaction.objects.create(user=self.other_user, name="Alheia", value=Decimal("200"), transaction_type="DEPOSIT", conta=self.conta)
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        all_transactions = [t for group in response.context["groups"] for t in group["transactions"]]
        self.assertEqual(len(all_transactions), 1)
        self.assertEqual(all_transactions[0].name, "Minha")

    def test_balance_calculation(self):
        Transaction.objects.create(user=self.user, name="Entrada", value=Decimal("300"), transaction_type="DEPOSIT", conta=self.conta)
        Transaction.objects.create(user=self.user, name="Saída", value=Decimal("100"), transaction_type="WITHDRAWAL", conta=self.conta)
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.context["saldo"], Decimal("200"))

    def test_balance_is_zero_with_no_transactions(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.context["saldo"], 0)

    def test_month_navigation_underflow(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"year": 2024, "month": 0})
        self.assertEqual(response.context["month_name"], "Dezembro")
        self.assertEqual(response.context["year"], 2023)

    def test_month_navigation_overflow(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"year": 2024, "month": 13})
        self.assertEqual(response.context["month_name"], "Janeiro")
        self.assertEqual(response.context["year"], 2025)

    def test_invalid_month_param_falls_back_to_current(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"year": "abc", "month": "xyz"})
        self.assertEqual(response.status_code, 200)
        today = date.today()
        self.assertEqual(response.context["year"], today.year)

    def test_monthly_balance_only_counts_selected_month(self):
        today = date.today()
        Transaction.objects.create(user=self.user, name="Este mês", value=Decimal("100"), transaction_type="DEPOSIT", conta=self.conta)
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"year": today.year, "month": today.month})
        self.assertEqual(response.context["balanco_mensal"], Decimal("100"))

    def test_today_label_in_groups(self):
        today = date.today()
        Transaction.objects.create(user=self.user, name="Hoje", value=Decimal("10"), transaction_type="DEPOSIT", conta=self.conta)
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"year": today.year, "month": today.month})
        labels = [g["label"] for g in response.context["groups"]]
        self.assertTrue(any(label.startswith("Hoje") for label in labels))

    def test_yesterday_label_in_groups(self):
        yesterday = date.today() - timedelta(days=1)
        with patch("apps.transactions.views.date") as mock_date:
            mock_date.today.return_value = date.today()
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            Transaction.objects.create(
                user=self.user, name="Ontem", value=Decimal("10"), transaction_type="DEPOSIT", conta=self.conta
            )
            t = Transaction.objects.get(name="Ontem")
            Transaction.objects.filter(pk=t.pk).update(date=yesterday)

        self.client.login(username="testuser", password="pass")
        today = date.today()
        response = self.client.get(self.url, {"year": today.year, "month": today.month})
        labels = [g["label"] for g in response.context["groups"]]
        self.assertTrue(any(label.startswith("Ontem") for label in labels))

    def test_prev_next_month_navigation_context(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"year": 2024, "month": 6})
        self.assertEqual(response.context["prev_month"], 5)
        self.assertEqual(response.context["next_month"], 7)
        self.assertEqual(response.context["prev_year"], 2024)
        self.assertEqual(response.context["next_year"], 2024)

    def test_prev_next_month_year_wrap(self):
        self.client.login(username="testuser", password="pass")
        response = self.client.get(self.url, {"year": 2024, "month": 1})
        self.assertEqual(response.context["prev_month"], 12)
        self.assertEqual(response.context["prev_year"], 2023)
        response = self.client.get(self.url, {"year": 2024, "month": 12})
        self.assertEqual(response.context["next_month"], 1)
        self.assertEqual(response.context["next_year"], 2025)