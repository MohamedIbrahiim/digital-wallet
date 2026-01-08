from django.test import TestCase
from rest_framework.test import APIRequestFactory

from shared.tests.factories import create_user, create_wallet
from wallets.permissions import IsWalletOwner


class IsWalletOwnerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsWalletOwner()

    def test_allows_owner(self):
        wallet = create_wallet()
        request = self.factory.get("/")
        request.user = wallet.user

        self.assertTrue(self.permission.has_object_permission(request, None, wallet))

    def test_denies_non_owner(self):
        wallet = create_wallet()
        other_user = create_user()
        request = self.factory.get("/")
        request.user = other_user

        self.assertFalse(self.permission.has_object_permission(request, None, wallet))
