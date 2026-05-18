from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from .base import E2EBaseTest
from apps.bank_accounts.models import Conta, Bank


@tag("e2e")
class TransactionsE2ETest(E2EBaseTest):
    def setUp(self):
        self.user = self.create_user()
        self.login_via_ui()
        self.bank = Bank.objects.create(name="Test Bank")
        self.conta = Conta.objects.create(bank=self.bank, usuario=self.user, account_type="corrente", number="12345")

    def _fill_transaction_form(self, tx_type, name, value):
        self.goto("transactions:create_transaction")
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=transaction_type]")
        ).select_by_value(tx_type)
        name_input = self.driver.find_element(By.ID, "name-input")
        name_input.clear()
        name_input.send_keys(name)
        # Set value via JS to bypass the locale-dependent input formatter
        self.driver.execute_script(
            f"document.getElementById('value-input').value = '{value}';"
        )
        # Clear the default category_id so no invalid FK is sent
        self.driver.execute_script(
            "document.getElementById('selected-category').value = '';"
        )
        # Select conta
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=conta_id]")
        ).select_by_value(str(self.conta.id))
        create_url = self.driver.current_url
        self.driver.find_element(By.ID, "sent-transaction-btn").click()
        # Wait for redirect away from the create page
        self.wait().until(EC.url_changes(create_url))

    def test_create_deposit_appears_in_list(self):
        """Creating a DEPOSIT transaction redirects to list and shows the entry."""
        self._fill_transaction_form("DEPOSIT", "Salário Teste", "2500.00")

        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Salário Teste", body_text)

    def test_create_withdrawal_appears_in_list(self):
        """Creating a WITHDRAWAL transaction redirects to list and shows the entry."""
        self._fill_transaction_form("WITHDRAWAL", "Conta de Luz", "180.00")

        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Conta de Luz", body_text)

    def test_missing_field_shows_validation_error(self):
        """Submitting the transaction form without a name shows a validation error."""
        self.goto("transactions:create_transaction")
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=transaction_type]")
        ).select_by_value("DEPOSIT")
        # Remove the required attribute so the browser does not block submission
        self.driver.execute_script(
            "document.getElementById('name-input').removeAttribute('required');"
        )
        self.driver.execute_script(
            "document.getElementById('selected-category').value = '';"
        )
        # Select conta
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=conta_id]")
        ).select_by_value(str(self.conta.id))
        value_input = self.driver.find_element(By.ID, "value-input")
        value_input.clear()
        value_input.send_keys("50.00")
        self.driver.find_element(By.ID, "sent-transaction-btn").click()

        self.wait().until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Informe o nome')]")
            )
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Informe o nome", body_text)

    def test_negative_value_shows_validation_error(self):
        """Submitting a transaction with a negative value shows a validation error."""
        self.goto("transactions:create_transaction")
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=transaction_type]")
        ).select_by_value("DEPOSIT")
        
        name_input = self.driver.find_element(By.ID, "name-input")
        name_input.clear()
        name_input.send_keys("Teste Negativo")
        
        self.driver.execute_script(
            "document.getElementById('selected-category').value = '';"
        )
        # Select conta
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=conta_id]")
        ).select_by_value(str(self.conta.id))
        
        value_input = self.driver.find_element(By.ID, "value-input")
        value_input.clear()
        
        self.driver.execute_script(
            "document.getElementById('value-input').value = '-50.00';"
        )
        
        self.driver.find_element(By.ID, "sent-transaction-btn").click()

        self.wait().until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'O valor deve ser maior que zero')]")
            )
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("O valor deve ser maior que zero", body_text)

    def test_max_character_limit_shows_validation_error(self):
        """Submitting a transaction name with > 150 characters shows a validation error."""
        self.goto("transactions:create_transaction")
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=transaction_type]")
        ).select_by_value("DEPOSIT")

        long_name = "A" * 151

        self.driver.execute_script(
            "document.getElementById('name-input').removeAttribute('maxlength');"
        )

        name_input = self.driver.find_element(By.ID, "name-input")
        name_input.clear()
        name_input.send_keys(long_name)

        self.driver.execute_script(
            "document.getElementById('selected-category').value = '';"
        )
        # Select conta
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=conta_id]")
        ).select_by_value(str(self.conta.id))

        self.driver.execute_script(
            "document.getElementById('value-input').value = '100.00';"
        )

        self.driver.find_element(By.ID, "sent-transaction-btn").click()

        self.wait().until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'O nome deve ter no máximo 150 caracteres')]")
            )
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("O nome deve ter no máximo 150 caracteres", body_text)

    def test_edit_transaction_shows_date_and_launch_type(self):
        """Editing a transaction shows date and launch type (Único/Recorrente) fields."""
        # Create a transaction first via API/model to avoid UI navigation complexity
        from apps.transactions.models import Transaction
        from django.urls import reverse

        tx = Transaction.objects.create(
            user=self.user,
            name="Test Transaction",
            transaction_type="WITHDRAWAL",
            value=100.00,
            conta=self.conta,
        )

        # Navigate directly to edit page using URL reverse
        edit_url = reverse('transactions:update', kwargs={'pk': tx.pk})
        self.driver.get(self.live_server_url + edit_url)

        # Wait for edit page to load
        self.wait().until(
            EC.presence_of_element_located((By.ID, "date-input"))
        )

        # Verify date field is present and editable
        date_input = self.driver.find_element(By.ID, "date-input")
        self.assertIsNotNone(date_input)
        self.assertTrue(date_input.get_attribute("type") == "date")

        # Verify launch type radio buttons are present
        radio_buttons = self.driver.find_elements(By.NAME, "is_fixed")
        self.assertEqual(len(radio_buttons), 2, "Should have 2 radio buttons for launch type")

        # Verify radio button values
        values = [btn.get_attribute("value") for btn in radio_buttons]
        self.assertIn("off", values)
        self.assertIn("on", values)

        # Verify radio button labels exist in page
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Tipo de Lançamento", body_text)
        self.assertIn("Único", body_text)
        self.assertIn("Recorrente", body_text)

    def test_category_modal_hides_date_and_launch_type(self):
        """Opening category modal hides date and launch type fields."""
        self.goto("transactions:create_transaction")
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=transaction_type]")
        ).select_by_value("WITHDRAWAL")

        name_input = self.driver.find_element(By.ID, "name-input")
        name_input.clear()
        name_input.send_keys("Test Transaction")

        self.driver.execute_script(
            "document.getElementById('selected-category').value = '';"
        )
        self.driver.execute_script(
            "document.getElementById('value-input').value = '100.00';"
        )
        # Select conta
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=conta_id]")
        ).select_by_value(str(self.conta.id))

        # Verify date and launch type are visible before opening modal
        date_container = self.driver.find_element(By.CLASS_NAME, "choose-date-container")
        recurring_container = self.driver.find_element(By.CLASS_NAME, "recurring-container")

        self.assertEqual(date_container.value_of_css_property("display"), "block")
        self.assertIn(recurring_container.value_of_css_property("display"), ["block", "flex"])

        # Open category modal
        self.driver.find_element(By.ID, "category-btn").click()

        # Wait for modal to be visible
        self.wait().until(
            EC.presence_of_element_located((By.ID, "category-modal"))
        )

        # Verify date and launch type are hidden
        self.assertEqual(date_container.value_of_css_property("display"), "none")
        self.assertEqual(recurring_container.value_of_css_property("display"), "none")

    def test_category_selection_shows_date_and_launch_type(self):
        """Selecting a category shows date and launch type fields again."""
        self.goto("transactions:create_transaction")
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=transaction_type]")
        ).select_by_value("WITHDRAWAL")

        name_input = self.driver.find_element(By.ID, "name-input")
        name_input.clear()
        name_input.send_keys("Test Transaction")

        self.driver.execute_script(
            "document.getElementById('selected-category').value = '';"
        )
        self.driver.execute_script(
            "document.getElementById('value-input').value = '100.00';"
        )
        # Select conta
        Select(
            self.driver.find_element(By.CSS_SELECTOR, "select[name=conta_id]")
        ).select_by_value(str(self.conta.id))

        # Get containers
        date_container = self.driver.find_element(By.CLASS_NAME, "choose-date-container")
        recurring_container = self.driver.find_element(By.CLASS_NAME, "recurring-container")

        # Open category modal
        self.driver.find_element(By.ID, "category-btn").click()

        # Wait for modal to be visible
        self.wait().until(
            EC.presence_of_element_located((By.ID, "category-modal"))
        )

        # Verify fields are hidden
        self.assertEqual(date_container.value_of_css_property("display"), "none")
        self.assertEqual(recurring_container.value_of_css_property("display"), "none")

        # Select first category
        categories = self.driver.find_elements(By.CLASS_NAME, "modal-option")
        if categories:
            categories[0].click()

            # Verify fields are visible again
            self.assertIn(date_container.value_of_css_property("display"), ["block", "flex"])
            self.assertIn(recurring_container.value_of_css_property("display"), ["block", "flex"])
