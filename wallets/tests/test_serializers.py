from django.test import TestCase
from rest_framework.test import APIRequestFactory

from shared.tests.factories import create_user, create_wallet
from wallets.serializers import WalletSerializer


class WalletSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = create_user()

    def test_validate_rejects_duplicate_name_for_user(self):
        create_wallet(user=self.user, name="Savings")

        request = self.factory.post("/wallets/")
        request.user = self.user

        serializer = WalletSerializer(
            data={"name": "Savings"},
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_create_assigns_user(self):
        request = self.factory.post("/wallets/")
        request.user = self.user

        serializer = WalletSerializer(
            data={"name": "Primary", "wallet_type": "current"},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        wallet = serializer.save()

        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.name, "Primary")
