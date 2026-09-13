from django.test import TestCase, Client, override_settings
from django.urls import reverse


class SignupProductionGuardTestCase(TestCase):
    """本番環境(DEBUG=False)で新規登録がサーバー側でも拒否されることのテスト"""

    def setUp(self):
        self.client = Client()

    @override_settings(DEBUG=False)
    def test_signup_post_is_forbidden_in_production(self):
        response = self.client.post(reverse('signup'), {
            'username': 'sneaky_user',
            'email': 'sneaky@example.com',
            'password1': 'SuperSecretPass123',
            'password2': 'SuperSecretPass123',
        })

        self.assertEqual(response.status_code, 403)

        from django.contrib.auth.models import User
        self.assertFalse(User.objects.filter(username='sneaky_user').exists())

    @override_settings(DEBUG=True)
    def test_signup_post_succeeds_in_debug(self):
        response = self.client.post(reverse('signup'), {
            'username': 'dev_user',
            'email': 'dev@example.com',
            'password1': 'SuperSecretPass123',
            'password2': 'SuperSecretPass123',
        })

        self.assertRedirects(response, reverse('login'))

        from django.contrib.auth.models import User
        self.assertTrue(User.objects.filter(username='dev_user').exists())
