from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from shared.tests.factories import create_wallet, create_user
from wallets.apis import WalletViewSet
from wallets.serializers import WalletSerializer


class WalletViewSetTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = create_user()

    def test_get_queryset_scopes_to_user(self):
        create_wallet(user=self.user)
        create_wallet(user=create_user())

        request = self.factory.get("/wallets/")
        request.user = self.user
        view = WalletViewSet()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)

    def test_get_serializer_class_for_create(self):
        view = WalletViewSet()
        view.action = "create"
        self.assertIs(view.get_serializer_class(), WalletSerializer)

    def test_get_serializer_class_for_retrieve(self):
        view = WalletViewSet()
        view.action = "retrieve"
        self.assertIs(view.get_serializer_class(), WalletSerializer)

    def test_retrieve_wallet(self):
        wallet = create_wallet(user=self.user)
        request = self.factory.get(f"/wallets/{wallet.reference_tag}/")
        force_authenticate(request, user=self.user)

        view = WalletViewSet.as_view({"get": "retrieve"})
        response = view(request, reference_tag=wallet.reference_tag)

        self.assertEqual(response.status_code, 200)

    def test_create_wallet(self):
        payload = {"name": "Primary", "wallet_type": "current"}
        request = self.factory.post("/wallets/", payload, format="json")
        force_authenticate(request, user=self.user)

        view = WalletViewSet.as_view({"post": "create"})
        response = view(request)

        self.assertEqual(response.status_code, 201)
