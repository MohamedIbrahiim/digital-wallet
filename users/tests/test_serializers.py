from django.test import TestCase
from rest_framework.test import APIRequestFactory

from users.serializers import ChangePasscodeSerializer, RegisterSerializer
from shared.tests.factories import create_user


class RegisterSerializerTests(TestCase):
    def test_register_creates_user_with_hashed_password(self):
        data = {
            "mobile_number": "+201234567890",
            "first_name": "Mona",
            "last_name": "Ibrahim",
            "passcode": "123456",
            "passcode_confirm": "123456",
        }

        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(str(user.mobile_number), data["mobile_number"])
        self.assertTrue(user.check_password(data["passcode"]))
        self.assertFalse(user.check_password("000000"))

    def test_register_rejects_mismatched_passcode(self):
        data = {
            "mobile_number": "+201234567890",
            "first_name": "Mona",
            "last_name": "Ibrahim",
            "passcode": "123456",
            "passcode_confirm": "654321",
        }

        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("passcode_confirm", serializer.errors)


class ChangePasscodeSerializerTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.factory = APIRequestFactory()

    def _request(self):
        request = self.factory.post("/api/v1/auth/change-passcode/")
        request.user = self.user
        return request

    def test_change_passcode_updates_password_and_token_version(self):
        data = {
            "old_passcode": "123456",
            "new_passcode": "654321",
            "new_passcode_confirm": "654321",
        }

        serializer = ChangePasscodeSerializer(
            data=data, context={"request": self._request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("654321"))
        self.assertEqual(self.user.token_version, 2)

    def test_change_passcode_rejects_incorrect_old_passcode(self):
        data = {
            "old_passcode": "000000",
            "new_passcode": "654321",
            "new_passcode_confirm": "654321",
        }

        serializer = ChangePasscodeSerializer(
            data=data, context={"request": self._request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_passcode", serializer.errors)

    def test_change_passcode_rejects_mismatched_new_passcode(self):
        data = {
            "old_passcode": "123456",
            "new_passcode": "654321",
            "new_passcode_confirm": "123456",
        }

        serializer = ChangePasscodeSerializer(
            data=data, context={"request": self._request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_passcode_confirm", serializer.errors)
