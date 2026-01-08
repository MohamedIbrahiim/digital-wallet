from django.test import TestCase

from shared.tests.factories import create_superuser, create_user


class UserManagerTests(TestCase):
    def test_create_superuser_sets_flags(self):
        user = create_superuser()

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)


class UserModelTests(TestCase):
    def test_user_str_returns_mobile_number(self):
        user = create_user()

        self.assertEqual(str(user), str(user.mobile_number))
