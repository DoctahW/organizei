from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base import E2EBaseTest


@tag("e2e")
class BankAccountsE2ETest(E2EBaseTest):
    def setUp(self):
        self.user = self.create_user()
        self.login_via_ui()

    def test_missing_bank_name_shows_validation_error(self):
        """Submitting a bank account without a bank name shows a validation error."""
        self.goto("register_manual")
        
        self.driver.execute_script(
            "document.querySelector('input[name=bank]').removeAttribute('required');"
        )
        self.driver.execute_script(
            "document.querySelector('input[name=number]').removeAttribute('required');"
        )

        self.driver.find_element(By.NAME, "number").send_keys("123456")
        
        self.driver.find_element(By.CSS_SELECTOR, ".button-glass--active").click()

        self.wait().until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'O nome do banco é obrigatório')]")
            )
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("O nome do banco é obrigatório", body_text)

    def test_missing_account_number_shows_validation_error(self):
        """Submitting a bank account without a number shows a validation error."""
        self.goto("register_manual")
        
        
        self.driver.execute_script(
            "document.querySelector('input[name=bank]').removeAttribute('required');"
        )
        self.driver.execute_script(
            "document.querySelector('input[name=number]').removeAttribute('required');"
        )
        
        self.driver.find_element(By.NAME, "bank").send_keys("Nubank")
        self.driver.find_element(By.CSS_SELECTOR, ".button-glass--active").click()

        self.wait().until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'O número da conta é obrigatório')]")
            )
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("O número da conta é obrigatório", body_text)
