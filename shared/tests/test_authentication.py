from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken

from shared.auth.authentication import VersionedJWTAuthentication

User = get_user_model()


class VersionedJWTAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            mobile_number="+201234567804", password="123456"
        )
        self.auth = VersionedJWTAuthentication()

    def test_get_user_accepts_matching_token_version(self):
        token = AccessToken.for_user(self.user)
        token["tv"] = self.user.token_version

        result = self.auth.get_user(token)
        self.assertEqual(result, self.user)

    def test_get_user_rejects_missing_token_version(self):
        token = AccessToken.for_user(self.user)

        with self.assertRaises(AuthenticationFailed):
            self.auth.get_user(token)

    def test_get_user_rejects_mismatched_token_version(self):
        token = AccessToken.for_user(self.user)
        token["tv"] = self.user.token_version + 1

        with self.assertRaises(AuthenticationFailed):
            self.auth.get_user(token)
