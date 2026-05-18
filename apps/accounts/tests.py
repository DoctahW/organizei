from django.contrib.auth.models import User
from django.test import Client, TestCase


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
        )

    def test_login_success(self):
        response = self.client.post(
            "/accounts/login/",
            {"form_type": "login", "username": "testuser", "password": "testpass123"},
        )
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)

    def test_login_failure(self):
        response = self.client.post(
            "/accounts/login/",
            {"form_type": "login", "username": "testuser", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)
        self.assertEqual(response.context["error"], "Usuário ou senha inválidos.")

    def test_register_success(self):
        response = self.client.post(
            "/accounts/register/",
            {
                "form_type": "register",
                "full_name": "New User",
                "email": "new@example.com",
                "password": "newpass123",
                "confirm_password": "newpass123",
            },
        )
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username="new@example.com").exists())
        user = User.objects.get(username="new@example.com")
        self.assertEqual(user.first_name, "New User")
        self.assertEqual(user.email, "new@example.com")

    def test_register_duplicate_username(self):
        User.objects.create_user(
            username="dup@example.com",
            email="dup@example.com",
            password="testpass123",
        )
        response = self.client.post(
            "/accounts/register/",
            {
                "form_type": "register",
                "full_name": "Dup User",
                "email": "dup@example.com",
                "password": "newpass123",
                "confirm_password": "newpass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("errors", response.context)
        self.assertIn("Este email já está cadastrado.", response.context["errors"])

    def test_register_password_mismatch(self):
        response = self.client.post(
            "/accounts/register/",
            {
                "form_type": "register",
                "full_name": "Mismatch User",
                "email": "mismatch@example.com",
                "password": "password123",
                "confirm_password": "different123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("errors", response.context)
        self.assertIn("As senhas não coincidem.", response.context["errors"])

    def test_profile_update(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            "/accounts/profile/",
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "updated@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertTrue(response.context["saved"])

    def test_password_change_success(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            "/accounts/password_change/",
            {
                "old_password": "testpass123",
                "new_password": "newsecurepass",
                "confirm_password": "newsecurepass",
            },
        )
        self.assertRedirects(
            response,
            "/accounts/password_change/done/",
            fetch_redirect_response=False,
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecurepass"))

    def test_password_change_wrong_old(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            "/accounts/password_change/",
            {
                "old_password": "wrongoldpass",
                "new_password": "newsecurepass",
                "confirm_password": "newsecurepass",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("errors", response.context)
        self.assertIn("Senha atual incorreta.", response.context["errors"])

    # --- Security / edge-case tests ---

    def test_login_open_redirect(self):
        """POST with next=https://evil.com should redirect to /dashboard/."""
        response = self.client.post(
            "/accounts/login/",
            {
                "form_type": "login",
                "username": "testuser",
                "password": "testpass123",
                "next": "https://evil.com",
            },
        )
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)

    def test_logout_get_request(self):
        """GET to logout should return 405 (Method Not Allowed)."""
        response = self.client.get("/accounts/logout/")
        self.assertEqual(response.status_code, 405)

    def test_register_short_password(self):
        """Password '123' should be rejected."""
        response = self.client.post(
            "/accounts/register/",
            {
                "form_type": "register",
                "full_name": "Short Pass",
                "email": "short@example.com",
                "password": "123",
                "confirm_password": "123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("errors", response.context)
        self.assertIn("Senha deve ter pelo menos 8 caracteres.", response.context["errors"])

    def test_register_invalid_email(self):
        """Email 'notanemail' should be rejected."""
        response = self.client.post(
            "/accounts/register/",
            {
                "form_type": "register",
                "full_name": "Bad Email",
                "email": "notanemail",
                "password": "validpass123",
                "confirm_password": "validpass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("errors", response.context)
        self.assertIn("Email inválido.", response.context["errors"])

    def test_profile_login_required(self):
        """GET /accounts/profile/ while logged out should redirect to login."""
        response = self.client.get("/accounts/profile/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
