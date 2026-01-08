from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from users.apis import ChangePasscodeView, RegisterView
from shared.tests.factories import create_user

User = get_user_model()


class RegisterViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_register_view_creates_user(self):
        payload = {
            "mobile_number": "+201234567800",
            "first_name": "Nora",
            "last_name": "Ali",
            "passcode": "907284",
            "passcode_confirm": "907284",
        }

        request = self.factory.post("/api/v1/auth/register/", payload, format="json")
        response = RegisterView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            User.objects.filter(mobile_number=payload["mobile_number"]).exists()
        )


class ChangePasscodeViewTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.factory = APIRequestFactory()

    def test_change_passcode_view_returns_success(self):
        payload = {
            "old_passcode": "123456",
            "new_passcode": "907284",
            "new_passcode_confirm": "907284",
        }

        request = self.factory.post(
            "/api/v1/auth/change-passcode/", payload, format="json"
        )
        force_authenticate(request, user=self.user)
        response = ChangePasscodeView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "Passcode changed successfully.")
