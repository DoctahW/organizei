from datetime import date

from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from apps.transactions.models import Transaction
from apps.bank_accounts.models import Conta, Bank

from .base import E2EBaseTest


@tag("e2e")
class BudgetE2ETest(E2EBaseTest):
    def setUp(self):
        self.user = self.create_user()
        self.login_via_ui()
        self.bank = Bank.objects.create(name="Test Bank")
        self.conta = Conta.objects.create(bank=self.bank, usuario=self.user, account_type="corrente", number="12345")

    def _set_budget_via_ui(self, limit_value):
        self.goto("budget:set_budget")
        limit_input = self.driver.find_element(By.ID, "limit")
        limit_input.clear()
        limit_input.send_keys(str(limit_value))
        set_url = self.driver.current_url
        self.driver.find_element(By.CSS_SELECTOR, ".button-glass--primary").click()
        # Wait until we leave the set_budget page (redirected to list)
        self.wait().until(EC.url_changes(set_url))

    def _create_withdrawal(self, amount):
        Transaction.objects.create(
            user=self.user,
            name="Gasto teste",
            value=amount,
            transaction_type="WITHDRAWAL",
            date=date.today(),
            conta=self.conta,
        )

    def test_define_limit_and_see_percentage(self):
        """Setting a budget limit displays the percentage on the budget page."""
        self._create_withdrawal(200)
        self._set_budget_via_ui(1000)

        self.goto("budget:list")
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("1000", body_text)
        self.assertIn("%", body_text)

    def test_alert_yellow_at_80_percent(self):
        """80 %+ spending shows the warning (yellow) state on the budget page."""
        self._set_budget_via_ui(1000)
        self._create_withdrawal(850)  # 85 % of 1000

        self.goto("budget:list")
        self.wait().until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".budget-progress__bar-fill"))
        )
        bar = self.driver.find_element(By.CSS_SELECTOR, ".budget-progress__bar-fill")
        classes = bar.get_attribute("class")
        self.assertIn("bg-warning", classes)

    def test_alert_red_when_exceeded(self):
        """100 %+ spending shows the danger (red) state on the budget page."""
        self._set_budget_via_ui(500)
        self._create_withdrawal(600)  # 120 % of 500

        self.goto("budget:list")
        self.wait().until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".budget-progress__bar-fill"))
        )
        bar = self.driver.find_element(By.CSS_SELECTOR, ".budget-progress__bar-fill")
        classes = bar.get_attribute("class")
        self.assertIn("bg-danger", classes)
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("ultrapassado", body_text.lower())

    def test_missing_limit_shows_validation_error(self):
        """Submitting an empty budget limit shows a validation error."""
        self.goto("budget:set_budget")
        
        self.driver.execute_script(
            "document.getElementById('limit').removeAttribute('required');"
        )
        
        limit_input = self.driver.find_element(By.ID, "limit")
        limit_input.clear()
        
        self.driver.find_element(By.CSS_SELECTOR, ".button-glass--primary").click()

        self.wait().until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'O limite é obrigatório')]")
            )
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("O limite é obrigatório", body_text)

    def test_negative_limit_shows_validation_error(self):
        """Submitting a negative budget limit shows a validation error."""
        self.goto("budget:set_budget")
        
        limit_input = self.driver.find_element(By.ID, "limit")
        limit_input.clear()
        
        self.driver.execute_script(
            "var el = document.getElementById('limit');"
            "el.removeAttribute('min');"
            "el.value = '-50';"
        )
        
        self.driver.find_element(By.CSS_SELECTOR, ".button-glass--primary").click()

        self.wait().until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'O limite deve ser maior que zero')]")
            )
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("O limite deve ser maior que zero", body_text)

    def test_invalid_limit_format_shows_validation_error(self):
        """Submitting an invalid number format shows a validation error."""
        self.goto("budget:set_budget")
        
        self.driver.execute_script(
            "document.getElementById('limit').type = 'text';"
        )
        
        limit_input = self.driver.find_element(By.ID, "limit")
        limit_input.clear()
        limit_input.send_keys("abc")
        
        self.driver.find_element(By.CSS_SELECTOR, ".button-glass--primary").click()

        self.wait().until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Informe um valor válido')]")
            )
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Informe um valor válido", body_text)
