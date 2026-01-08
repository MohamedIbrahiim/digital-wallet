from django.test import TestCase

from django.contrib.auth import get_user_model

from shared.tests.factories import create_access_token_record, create_user


class UserAccessTokenTests(TestCase):
    def test_access_token_str(self):
        user = create_user()
        token = create_access_token_record(user=user, jti="token-1")

        self.assertEqual(str(token), f"{user.id}:token-1")


class UserManagerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_create_user_sets_password(self):
        user = self.User.objects.create_user(
            mobile_number="+201234567999", password="907284"
        )

        self.assertTrue(user.check_password("907284"))
        self.assertFalse(user.is_staff)

    def test_create_superuser_sets_flags(self):
        user = self.User.objects.create_superuser(
            mobile_number="+201234567998", password="907284"
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_user_str_returns_mobile_number(self):
        user = create_user(mobile_number="+201234567997")
        self.assertEqual(str(user), "+201234567997")
