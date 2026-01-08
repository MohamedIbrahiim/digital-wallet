from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate

from shared.tests.factories import create_user, create_wallet
from transactions.apis import (
    WalletDepositView,
    InternalTransferView,
    P2PSendHoldView,
    WalletTransactionHistoryView,
    UserTransactionHistoryView,
)


class TransactionApiTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = create_user()
        self.other_user = create_user()
        self.wallet = create_wallet(user=self.user, balance=Decimal("100.00"))
        self.other_wallet = create_wallet(
            user=self.other_user, balance=Decimal("50.00")
        )
        self.second_wallet = create_wallet(user=self.user, balance=Decimal("10.00"))

    def test_wallet_deposit(self):
        payload = {"amount": "10.00"}
        request = self.factory.post(
            f"/wallets/{self.wallet.reference_tag}/deposit/", payload, format="json"
        )
        force_authenticate(request, user=self.user)

        response = WalletDepositView.as_view()(
            request, reference_tag=self.wallet.reference_tag
        )

        self.assertEqual(response.status_code, 201)

    def test_wallet_deposit_rejects_wrong_owner(self):
        payload = {"amount": "10.00"}
        request = self.factory.post(
            f"/wallets/{self.wallet.reference_tag}/deposit/", payload, format="json"
        )
        force_authenticate(request, user=self.other_user)

        response = WalletDepositView.as_view()(
            request, reference_tag=self.wallet.reference_tag
        )

        self.assertEqual(response.status_code, 400)

    def test_internal_transfer(self):
        payload = {
            "from_reference_tag": self.wallet.reference_tag,
            "to_reference_tag": self.second_wallet.reference_tag,
            "amount": "5.00",
        }
        request = self.factory.post("/transactions/transfer/", payload, format="json")
        force_authenticate(request, user=self.user)

        response = InternalTransferView.as_view()(request)

        self.assertEqual(response.status_code, 201)

    def test_internal_transfer_insufficient_funds(self):
        payload = {
            "from_reference_tag": self.second_wallet.reference_tag,
            "to_reference_tag": self.wallet.reference_tag,
            "amount": "500.00",
        }
        request = self.factory.post("/transactions/transfer/", payload, format="json")
        force_authenticate(request, user=self.user)

        response = InternalTransferView.as_view()(request)

        self.assertEqual(response.status_code, 400)

    def test_p2p_send_hold(self):
        payload = {
            "from_reference_tag": self.wallet.reference_tag,
            "to_reference_tag": self.other_wallet.reference_tag,
            "amount": "7.00",
        }
        request = self.factory.post("/transactions/send/", payload, format="json")
        force_authenticate(request, user=self.user)

        response = P2PSendHoldView.as_view()(request)

        self.assertEqual(response.status_code, 201)

    def test_wallet_history_swagger_fake_view_returns_empty(self):
        request = self.factory.get(
            f"/wallets/{self.wallet.reference_tag}/transactions/"
        )
        request.user = self.user
        view = WalletTransactionHistoryView()
        view.request = request
        view.kwargs = {"reference_tag": self.wallet.reference_tag}
        view.swagger_fake_view = True

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 0)

    def test_wallet_history_missing_reference_tag_returns_empty(self):
        request = self.factory.get("/wallets/transactions/")
        request.user = self.user
        view = WalletTransactionHistoryView()
        view.request = request
        view.kwargs = {}

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 0)

    def test_user_history_anonymous_returns_empty(self):
        request = self.factory.get("/transactions/")
        request.user = AnonymousUser()
        view = UserTransactionHistoryView()
        view.request = request

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 0)

    def test_user_history_swagger_fake_view_returns_empty(self):
        request = self.factory.get("/transactions/")
        request.user = self.user
        view = UserTransactionHistoryView()
        view.request = request
        view.swagger_fake_view = True

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 0)
