from datetime import date
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from apps.subscriptions.models import Subscription
from apps.subscriptions.views import _generate_subscription_occurrences, _create_transactions_for_subscription
from apps.transactions.models import Transaction, Category


def make_user(username='testuser'):
    return User.objects.create_user(username=username, password='testpass')


def make_category():
    cat, _ = Category.objects.get_or_create(name='Assinatura', user=None)
    return cat


def make_subscription(user, name='Netflix', value='29.90', start_date=None, end_date=None):
    return Subscription.objects.create(
        user=user,
        name=name,
        value=value,
        start_date=start_date or date.today(),
        end_date=end_date,
    )

class GenerateOccurrencesTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_generates_exactly_12_occurrences(self):
        sub = make_subscription(self.user, start_date=date(2026, 1, 1))
        occurrences = _generate_subscription_occurrences(sub)
        self.assertEqual(len(occurrences), 12)

    def test_first_occurrence_is_start_date(self):
        start = date(2026, 3, 10)
        sub = make_subscription(self.user, start_date=start)
        occurrences = _generate_subscription_occurrences(sub)
        self.assertEqual(occurrences[0], start)

    def test_occurrences_are_monthly(self):
        start = date(2026, 1, 15)
        sub = make_subscription(self.user, start_date=start)
        occurrences = _generate_subscription_occurrences(sub)
        for i, occ in enumerate(occurrences):
            expected = start + relativedelta(months=i)
            self.assertEqual(occ, expected)

    def test_respects_end_date(self):
        start = date(2026, 1, 1)
        end = date(2026, 4, 30)
        sub = make_subscription(self.user, start_date=start, end_date=end)
        occurrences = _generate_subscription_occurrences(sub)
        self.assertEqual(len(occurrences), 4)
        for occ in occurrences:
            self.assertLessEqual(occ, end)

    def test_handles_month_overflow_day_31(self):
        start = date(2026, 1, 31)
        sub = make_subscription(self.user, start_date=start)
        occurrences = _generate_subscription_occurrences(sub)
        feb = occurrences[1]
        self.assertEqual(feb.month, 2)
        self.assertIn(feb.day, [28, 29])

    def test_no_occurrences_before_start_date(self):
        start = date(2026, 6, 1)
        sub = make_subscription(self.user, start_date=start)
        occurrences = _generate_subscription_occurrences(sub)
        for occ in occurrences:
            self.assertGreaterEqual(occ, start)

class CreateTransactionsForSubscriptionTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.category = make_category()

    def test_creates_correct_number_of_transactions(self):
        sub = make_subscription(self.user, start_date=date(2026, 1, 1))
        _create_transactions_for_subscription(sub, self.user)
        self.assertEqual(Transaction.objects.filter(subscription=sub).count(), 12)

    def test_transactions_are_withdrawals(self):
        sub = make_subscription(self.user, start_date=date(2026, 1, 1))
        _create_transactions_for_subscription(sub, self.user)
        types = Transaction.objects.filter(subscription=sub).values_list('transaction_type', flat=True)
        self.assertTrue(all(t == 'WITHDRAWAL' for t in types))

    def test_transactions_have_assinatura_category(self):
        sub = make_subscription(self.user, start_date=date(2026, 1, 1))
        _create_transactions_for_subscription(sub, self.user)
        categories = Transaction.objects.filter(subscription=sub).values_list('category__name', flat=True)
        self.assertTrue(all(c == 'Assinatura' for c in categories))

    def test_transactions_have_correct_value(self):
        sub = make_subscription(self.user, value='55.90', start_date=date(2026, 1, 1))
        _create_transactions_for_subscription(sub, self.user)
        values = Transaction.objects.filter(subscription=sub).values_list('value', flat=True)
        self.assertTrue(all(float(v) == 55.90 for v in values))

    def test_transactions_linked_to_subscription(self):
        sub = make_subscription(self.user, start_date=date(2026, 1, 1))
        _create_transactions_for_subscription(sub, self.user)
        linked = Transaction.objects.filter(subscription=sub).count()
        self.assertEqual(linked, 12)

    def test_transactions_marked_as_fixed(self):
        sub = make_subscription(self.user, start_date=date(2026, 1, 1))
        _create_transactions_for_subscription(sub, self.user)
        fixed = Transaction.objects.filter(subscription=sub, is_fixed=True).count()
        self.assertEqual(fixed, 12)

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ManageSubscriptionsViewTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
        self.category = make_category()
        self.url = reverse('subscriptions:manage_subscriptions')

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_subscription(self):
        self.client.post(self.url, {
            'name': 'Spotify',
            'value': '21,90',
            'start_date': '2026-01-01',
        })
        self.assertEqual(Subscription.objects.filter(user=self.user, name='Spotify').count(), 1)

    def test_post_generates_transactions(self):
        self.client.post(self.url, {
            'name': 'Spotify',
            'value': '21,90',
            'start_date': '2026-01-01',
        })
        sub = Subscription.objects.get(user=self.user, name='Spotify')
        self.assertEqual(Transaction.objects.filter(subscription=sub).count(), 12)

    def test_post_redirects_after_creation(self):
        response = self.client.post(self.url, {
            'name': 'Disney+',
            'value': '38,90',
            'start_date': '2026-01-01',
        })
        self.assertRedirects(response, self.url)

    def test_unauthenticated_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class DeleteSubscriptionViewTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
        self.category = make_category()
        self.sub = make_subscription(self.user, start_date=date(2026, 1, 1))
        _create_transactions_for_subscription(self.sub, self.user)

    def test_delete_removes_subscription(self):
        url = reverse('subscriptions:delete_subscription', args=[self.sub.pk])
        self.client.post(url)
        self.assertFalse(Subscription.objects.filter(pk=self.sub.pk).exists())

    def test_delete_cascades_to_transactions(self):
        url = reverse('subscriptions:delete_subscription', args=[self.sub.pk])
        self.client.post(url)
        self.assertEqual(Transaction.objects.filter(subscription=self.sub).count(), 0)

    def test_delete_only_affects_own_subscription(self):
        other_user = make_user('other')
        other_sub = make_subscription(other_user, start_date=date(2026, 1, 1))
        url = reverse('subscriptions:delete_subscription', args=[other_sub.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_get_does_not_delete(self):
        url = reverse('subscriptions:delete_subscription', args=[self.sub.pk])
        self.client.get(url)
        self.assertTrue(Subscription.objects.filter(pk=self.sub.pk).exists())