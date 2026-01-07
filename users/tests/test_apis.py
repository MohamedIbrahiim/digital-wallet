from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from users.apis import ChangePasscodeView, RegisterView

User = get_user_model()


class RegisterViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_register_view_creates_user(self):
        payload = {
            "mobile_number": "+201234567800",
            "first_name": "Nora",
            "last_name": "Ali",
            "passcode": "123456",
            "passcode_confirm": "123456",
        }

        request = self.factory.post("/api/v1/auth/register/", payload, format="json")
        response = RegisterView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            User.objects.filter(mobile_number=payload["mobile_number"]).exists()
        )


class ChangePasscodeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            mobile_number="+201234567801", password="123456"
        )
        self.factory = APIRequestFactory()

    def test_change_passcode_view_returns_success(self):
        payload = {
            "old_passcode": "123456",
            "new_passcode": "654321",
            "new_passcode_confirm": "654321",
        }

        request = self.factory.post(
            "/api/v1/auth/change-passcode/", payload, format="json"
        )
        force_authenticate(request, user=self.user)
        response = ChangePasscodeView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "Passcode changed successfully.")
