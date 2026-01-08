from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from shared.tests.factories import create_user
from transactions.apis import (
    InternalTransferView,
    P2PSendHoldView,
    TransactionActionView,
    WalletDepositView,
)
from transactions.models import Transaction, TransactionStatus
from wallets.apis import WalletViewSet
from wallets.models import Wallet


class TransactionFullFlowTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user1 = create_user()
        self.user2 = create_user()
        self.user3 = create_user()

        self.wallet1 = self._create_wallet(self.user1, "U1 Primary")
        self.wallet2a = self._create_wallet(self.user2, "U2 Main")
        self.wallet2b = self._create_wallet(self.user2, "U2 Savings")
        self.wallet3 = self._create_wallet(self.user3, "U3 Primary")

    def _create_wallet(self, user, name):
        payload = {"name": name, "wallet_type": "current"}
        request = self.factory.post("/wallets/", payload, format="json")
        force_authenticate(request, user=user)
        response = WalletViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)
        return Wallet.objects.get(pk=response.data["id"])

    def _deposit(self, user, wallet, amount):
        wallet.refresh_from_db()
        start_balance = wallet.balance

        payload = {"amount": str(amount)}
        request = self.factory.post(
            f"/wallets/{wallet.reference_tag}/deposit/", payload, format="json"
        )
        force_authenticate(request, user=user)
        response = WalletDepositView.as_view()(
            request, reference_tag=wallet.reference_tag
        )
        self.assertEqual(response.status_code, 201)

        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, start_balance + amount)

    def _transfer_internal(self, user, from_wallet, to_wallet, amount):
        from_wallet.refresh_from_db()
        to_wallet.refresh_from_db()
        from_start = from_wallet.balance
        to_start = to_wallet.balance

        payload = {
            "from_reference_tag": from_wallet.reference_tag,
            "to_reference_tag": to_wallet.reference_tag,
            "amount": str(amount),
        }
        request = self.factory.post("/wallets/transfer/", payload, format="json")
        force_authenticate(request, user=user)
        response = InternalTransferView.as_view()(request)
        self.assertEqual(response.status_code, 201)

        from_wallet.refresh_from_db()
        to_wallet.refresh_from_db()
        self.assertEqual(from_wallet.balance, from_start - amount)
        self.assertEqual(to_wallet.balance, to_start + amount)

    def _p2p_hold(self, user, from_wallet, to_wallet, amount):
        from_wallet.refresh_from_db()
        to_wallet.refresh_from_db()
        from_start = from_wallet.balance
        from_held_start = from_wallet.held_balance
        to_start = to_wallet.balance

        payload = {
            "from_reference_tag": from_wallet.reference_tag,
            "to_reference_tag": to_wallet.reference_tag,
            "amount": str(amount),
        }
        request = self.factory.post("/wallets/send/", payload, format="json")
        force_authenticate(request, user=user)
        response = P2PSendHoldView.as_view()(request)
        self.assertEqual(response.status_code, 201)

        from_wallet.refresh_from_db()
        to_wallet.refresh_from_db()
        self.assertEqual(from_wallet.balance, from_start - amount)
        self.assertEqual(from_wallet.held_balance, from_held_start + amount)
        self.assertEqual(to_wallet.balance, to_start)

        return response.data["id"]

    def _p2p_action(self, user, tx_id, is_accepted):
        payload = {"is_accepted": is_accepted}
        request = self.factory.post(
            f"/transactions/{tx_id}/action/", payload, format="json"
        )
        force_authenticate(request, user=user)
        response = TransactionActionView.as_view()(request, tx_id=tx_id)
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_full_transaction_flow(self):
        # Deposits
        self._deposit(self.user1, self.wallet1, Decimal("100.00"))
        self._deposit(self.user2, self.wallet2a, Decimal("200.00"))
        self._deposit(self.user2, self.wallet2b, Decimal("50.00"))
        self._deposit(self.user3, self.wallet3, Decimal("80.00"))

        # Internal transfer (user2)
        self._transfer_internal(
            self.user2, self.wallet2a, self.wallet2b, Decimal("30.00")
        )

        # P2P holds
        tx1 = self._p2p_hold(self.user1, self.wallet1, self.wallet2a, Decimal("10.00"))
        tx2 = self._p2p_hold(self.user2, self.wallet2a, self.wallet3, Decimal("15.00"))
        tx3 = self._p2p_hold(self.user3, self.wallet3, self.wallet1, Decimal("5.00"))

        # Actions: accept tx1, reject tx2, accept tx3
        self._p2p_action(self.user2, tx1, True)
        self._p2p_action(self.user3, tx2, False)
        self._p2p_action(self.user1, tx3, True)

        # Reload wallets for final balances
        self.wallet1.refresh_from_db()
        self.wallet2a.refresh_from_db()
        self.wallet2b.refresh_from_db()
        self.wallet3.refresh_from_db()

        self.assertEqual(self.wallet1.balance, Decimal("95.00"))
        self.assertEqual(self.wallet1.held_balance, Decimal("0.00"))

        self.assertEqual(self.wallet2a.balance, Decimal("180.00"))
        self.assertEqual(self.wallet2a.held_balance, Decimal("0.00"))

        self.assertEqual(self.wallet2b.balance, Decimal("80.00"))

        self.assertEqual(self.wallet3.balance, Decimal("75.00"))
        self.assertEqual(self.wallet3.held_balance, Decimal("0.00"))

        tx1_obj = Transaction.objects.get(pk=tx1)
        tx2_obj = Transaction.objects.get(pk=tx2)
        tx3_obj = Transaction.objects.get(pk=tx3)

        self.assertEqual(tx1_obj.status, TransactionStatus.COMPLETED)
        self.assertFalse(tx1_obj.is_hold)
        self.assertEqual(tx2_obj.status, TransactionStatus.REJECTED)
        self.assertFalse(tx2_obj.is_hold)
        self.assertEqual(tx3_obj.status, TransactionStatus.COMPLETED)
        self.assertFalse(tx3_obj.is_hold)
