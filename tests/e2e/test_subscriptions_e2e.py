from datetime import date
from django.test import tag, Client
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base import E2EBaseTest
from apps.subscriptions.models import Subscription
from apps.transactions.models import Transaction


@tag("e2e")
class SubscriptionsE2ETest(E2EBaseTest):
    def setUp(self):
        self.user = self.create_user()
        self.login_via_ui()
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def _create_subscription_via_form(self, name, start_date, value):
        """Create subscription via direct POST to the form (backend).

        Value should be in format '29,90' or '29.90' - the view will process it.
        """
        url = self.live_server_url + reverse('subscriptions:manage_subscriptions')
        response = self.client.post(url, {
            'name': name,
            'start_date': start_date,
            'value': value,  # value like "29,90" or "29.90"
        })
        # Verify redirect (successful POST)
        self.assertEqual(response.status_code, 302)

        # Refresh page in browser to see new subscription
        self.driver.get(url)
        return Subscription.objects.get(user=self.user, name=name)

    def test_create_subscription_from_management_page(self):
        """Creating a subscription appears in list and generates 12 transactions."""
        # Create subscription (value format: "29,90" - with comma, following Brazilian format)
        sub = self._create_subscription_via_form(
            name="Netflix Teste",
            start_date="2026-06-01",
            value="29,90"
        )

        # Navigate to subscriptions page
        self.goto("subscriptions:manage_subscriptions")

        # Verify subscription appears in list
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Netflix Teste", body_text)

        # Verify subscription attributes
        self.assertEqual(str(sub.value), "29.90")
        self.assertEqual(sub.start_date, date(2026, 6, 1))

        # Verify 12 transactions were created
        transactions = Transaction.objects.filter(
            user=self.user,
            subscription=sub
        )
        self.assertEqual(transactions.count(), 12)

        # Verify all transactions are marked as fixed and withdrawal
        for tx in transactions:
            self.assertTrue(tx.is_fixed)
            self.assertEqual(tx.transaction_type, 'WITHDRAWAL')

    def test_delete_subscription(self):
        """Deleting a subscription removes it from list and cascades to transactions."""
        # Create a subscription
        sub = self._create_subscription_via_form(
            name="Spotify Teste",
            start_date="2026-05-15",
            value="15,99"
        )

        # Navigate to subscriptions page
        self.goto("subscriptions:manage_subscriptions")

        # Verify subscription is on page
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Spotify Teste", body_text)

        # Click on the subscription to go to detail page
        sub_link = self.driver.find_element(By.XPATH, f"//p[contains(text(), 'Spotify Teste')]")
        sub_link.click()

        # Wait for subscription detail page to load
        self.wait().until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Excluir')]"))
        )

        # Click delete button
        delete_btn = self.driver.find_element(By.XPATH, "//button[contains(., 'Excluir')]")
        delete_btn.click()

        # Wait and handle potential confirmation or redirect
        # The delete view POSTs and redirects back to manage_subscriptions
        self.wait().until(EC.url_contains("assinaturas"))

        # Verify subscription no longer appears in list
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertNotIn("Spotify Teste", body_text)

        # Verify subscription was deleted from database
        self.assertFalse(Subscription.objects.filter(pk=sub.pk).exists())

        # Verify all associated transactions were deleted (cascade)
        self.assertEqual(
            Transaction.objects.filter(subscription=sub).count(),
            0
        )



