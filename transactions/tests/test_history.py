from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from shared.tests.factories import create_user, create_wallet
from transactions.apis import WalletTransactionHistoryView, UserTransactionHistoryView
from transactions.services import MoneyFlowService


class TransactionHistoryTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = create_user()
        self.other_user = create_user()
        self.wallet = create_wallet(user=self.user, balance=Decimal("100.00"))
        self.second_wallet = create_wallet(user=self.user, balance=Decimal("50.00"))
        self.other_wallet = create_wallet(
            user=self.other_user, balance=Decimal("10.00")
        )

        MoneyFlowService.deposit(
            user=self.user,
            wallet_id=self.wallet.id,
            amount=Decimal("10.00"),
        )

    def test_wallet_history_returns_results(self):
        request = self.factory.get(
            f"/wallets/{self.wallet.reference_tag}/transactions/"
        )
        force_authenticate(request, user=self.user)

        response = WalletTransactionHistoryView.as_view()(
            request, reference_tag=self.wallet.reference_tag
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) >= 1)

    def test_wallet_history_rejects_invalid_tag(self):
        request = self.factory.get("/wallets/@wlt_missing.999/transactions/")
        force_authenticate(request, user=self.user)

        response = WalletTransactionHistoryView.as_view()(
            request, reference_tag="@wlt_missing.999"
        )

        self.assertEqual(response.status_code, 400)

    def test_user_history_without_wallet_tag(self):
        request = self.factory.get("/transactions/")
        force_authenticate(request, user=self.user)

        response = UserTransactionHistoryView.as_view()(request)

        self.assertEqual(response.status_code, 200)

    def test_user_history_with_wallet_tag(self):
        request = self.factory.get(
            f"/transactions/?wallet_tag={self.wallet.reference_tag}"
        )
        force_authenticate(request, user=self.user)

        response = UserTransactionHistoryView.as_view()(request)

        self.assertEqual(response.status_code, 200)

    def test_user_history_rejects_invalid_wallet_tag(self):
        request = self.factory.get("/transactions/?wallet_tag=@wlt_missing.999")
        force_authenticate(request, user=self.user)

        response = UserTransactionHistoryView.as_view()(request)

        self.assertEqual(response.status_code, 400)
