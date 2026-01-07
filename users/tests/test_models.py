from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserManagerTests(TestCase):
    def test_create_superuser_sets_flags(self):
        user = User.objects.create_superuser(
            mobile_number="+201234567802", password="123456"
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)


class UserModelTests(TestCase):
    def test_user_str_returns_mobile_number(self):
        user = User.objects.create_user(
            mobile_number="+201234567803", password="123456"
        )

        self.assertEqual(str(user), "+201234567803")
