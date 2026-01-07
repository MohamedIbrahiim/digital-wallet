from django.contrib.auth import get_user_model
from django.test import TestCase

from shared.auth.serializers import LoginSerializer

User = get_user_model()


class LoginSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            mobile_number="+201234567805", password="123456"
        )

    def test_get_token_includes_token_version(self):
        token = LoginSerializer.get_token(self.user)
        self.assertEqual(token["tv"], self.user.token_version)

    def test_validate_removes_refresh(self):
        serializer = LoginSerializer(
            data={"mobile_number": "+201234567805", "password": "123456"}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn("access", serializer.validated_data)
        self.assertNotIn("refresh", serializer.validated_data)
