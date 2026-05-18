from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base import E2EBaseTest


@tag("e2e")
class AccountsE2ETest(E2EBaseTest):
    def test_register_then_login_flow(self):
        """User created in DB can log in and is redirected to the dashboard."""
        self.create_user(username="newuser", password="securepass99")

        self.login_via_ui(username="newuser", password="securepass99")

        # Default post-login redirect is /metas/; just confirm we left the login page
        self.assertNotIn("/accounts/login/", self.driver.current_url)

    def test_login_invalid_credentials_shows_error(self):
        """Wrong password renders the login page with an error message."""
        self.create_user(username="validuser", password="correctpass")

        self.driver.get(f"{self.live_server_url}/accounts/login/")
        self.wait().until(EC.presence_of_element_located((By.ID, "login-username")))
        self.driver.find_element(By.ID, "login-username").send_keys("validuser")
        self.driver.find_element(By.ID, "login-password").send_keys("wrongpass")
        self.driver.find_element(By.CSS_SELECTOR, "#login-panel .auth-form__btn").click()

        self.wait().until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-errors"))
        )
        error_text = self.driver.find_element(By.CSS_SELECTOR, ".auth-errors").text
        self.assertIn("inválidos", error_text.lower())

    def test_logout_redirects_to_login(self):
        """After logging out the user lands on the login page."""
        self.create_user()
        self.login_via_ui()

        self.driver.find_element(
            By.CSS_SELECTOR, ".navbar__logout-form button[type='submit']"
        ).click()

        self.wait().until(EC.url_contains("/accounts/login/"))
        self.assertIn("/accounts/login/", self.driver.current_url)
