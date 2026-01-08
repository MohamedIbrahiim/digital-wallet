from django.test import TestCase
from rest_framework.test import APIRequestFactory

from shared.auth.serializers import LoginSerializer
from shared.tests.factories import create_user


class LoginSerializerTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
        self.factory = APIRequestFactory()

    def test_get_token_includes_token_version(self):
        token = LoginSerializer.get_token(self.user)
        self.assertEqual(token["tv"], self.user.token_version)

    def test_validate_removes_refresh(self):
        request = self.factory.post("/api/v1/auth/login/")
        serializer = LoginSerializer(
            data={"mobile_number": str(self.user.mobile_number), "password": "123456"},
            context={"request": request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn("access", serializer.validated_data)
        self.assertNotIn("refresh", serializer.validated_data)
