from django.test import TestCase
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken

from shared.auth.authentication import VersionedJWTAuthentication
from shared.tests.factories import create_user, create_access_token_record


class VersionedJWTAuthenticationTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.auth = VersionedJWTAuthentication()

    def test_get_user_accepts_matching_token_version(self):
        token = AccessToken.for_user(self.user)
        token["tv"] = self.user.token_version
        create_access_token_record(user=self.user, jti=str(token["jti"]))

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

    def test_get_user_rejects_missing_jti(self):
        token = AccessToken.for_user(self.user)
        token["tv"] = self.user.token_version
        token.payload.pop("jti", None)

        with self.assertRaises(AuthenticationFailed):
            self.auth.get_user(token)

    def test_get_user_rejects_expired_session(self):
        token = AccessToken.for_user(self.user)
        token["tv"] = self.user.token_version
        create_access_token_record(
            user=self.user, jti=str(token["jti"]), expires_in_seconds=-1
        )

        with self.assertRaises(AuthenticationFailed):
            self.auth.get_user(token)
