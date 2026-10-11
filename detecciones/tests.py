from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


class AuthenticationAndLandingTests(TestCase):
    """
    Test suite for user model, bcrypt password hasher, views, and authentication flow.
    """

    def setUp(self):
        self.client = Client()
        # Create users via the seed command to verify both the command and model
        call_command('seed_users')

    def test_seed_users_created_with_bcrypt(self):
        """Verify seeded users exist with correct roles, phones, and bcrypt hashes."""
        lolo = User.objects.get(username='lolo')
        pablito = User.objects.get(username='pablito')

        self.assertEqual(lolo.first_name, 'Lolo')
        self.assertEqual(lolo.phone, '123456789')
        self.assertEqual(lolo.role, 'admin')
        self.assertTrue(lolo.is_admin())
        self.assertTrue(lolo.password.startswith('bcrypt'))

        self.assertEqual(pablito.first_name, 'Pablito')
        self.assertEqual(pablito.phone, '987654321')
        self.assertEqual(pablito.role, 'operator')
        self.assertTrue(pablito.is_operator())
        self.assertTrue(pablito.password.startswith('bcrypt'))

    def test_landing_page_renders_for_unauthenticated_user(self):
        """Verify landing page at '/' is accessible and contains 'Iniciar Sesión'."""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar Sesión')
        self.assertContains(response, 'Brazo Robot')
        self.assertContains(response, 'Clasificación')

    def test_dashboard_requires_login(self):
        """Verify accessing /dashboard/ without login redirects to /login/."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_login_with_invalid_credentials(self):
        """Verify login failure renders error message in Spanish."""
        response = self.client.post(reverse('login'), {
            'username': 'lolo',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos')

    def test_login_successful_and_redirects_to_dashboard(self):
        """Verify valid login authenticates user and redirects to /dashboard/."""
        response = self.client.post(reverse('login'), {
            'username': 'lolo',
            'password': 'admin123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lolo')
        self.assertContains(response, 'Cerrar Sesión')
        self.assertContains(response, 'Monitoreo de Residuos')

    def test_logout_redirects_to_landing_page(self):
        """Verify logout view logs user out and redirects to landing page."""
        # Log in first
        self.client.login(username='pablito', password='admin123')
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar Sesión')
