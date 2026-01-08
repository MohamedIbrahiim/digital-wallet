from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError
from types import SimpleNamespace
from unittest import mock

from rest_framework.test import APIRequestFactory, force_authenticate

from shared.tests.factories import create_user, create_wallet
from transactions.apis import TransactionActionView
from transactions.models import Transaction, TransactionType, TransactionStatus
from transactions.services import MoneyFlowService
from wallets.models import WalletStatus


class TransactionActionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.sender = create_user()
        self.recipient = create_user()
        self.sender_wallet = create_wallet(user=self.sender, balance=Decimal("100.00"))
        self.recipient_wallet = create_wallet(
            user=self.recipient, balance=Decimal("10.00")
        )

        self.tx = MoneyFlowService.p2p_send_hold(
            user=self.sender,
            from_reference_tag=self.sender_wallet.reference_tag,
            to_reference_tag=self.recipient_wallet.reference_tag,
            amount=Decimal("20.00"),
        )

    def test_accept_p2p(self):
        payload = {"is_accepted": True}
        request = self.factory.post(
            f"/transactions/{self.tx.id}/action/", payload, format="json"
        )
        force_authenticate(request, user=self.recipient)

        response = TransactionActionView.as_view()(request, tx_id=self.tx.id)

        self.assertEqual(response.status_code, 200)

    def test_reject_p2p(self):
        tx = MoneyFlowService.p2p_send_hold(
            user=self.sender,
            from_reference_tag=self.sender_wallet.reference_tag,
            to_reference_tag=self.recipient_wallet.reference_tag,
            amount=Decimal("5.00"),
        )
        payload = {"is_accepted": False}
        request = self.factory.post(
            f"/transactions/{tx.id}/action/", payload, format="json"
        )
        force_authenticate(request, user=self.recipient)

        response = TransactionActionView.as_view()(request, tx_id=tx.id)

        self.assertEqual(response.status_code, 200)

    def test_accept_reject_requires_recipient(self):
        with self.assertRaises(PermissionDenied):
            MoneyFlowService.p2p_accept(user=self.sender, tx_id=self.tx.id)

    def test_accept_requires_pending(self):
        self.tx.status = TransactionStatus.COMPLETED
        self.tx.is_hold = False
        self.tx.save(update_fields=["status", "is_hold"])

        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_accept(user=self.recipient, tx_id=self.tx.id)

    def test_reject_requires_pending(self):
        self.tx.status = TransactionStatus.COMPLETED
        self.tx.is_hold = False
        self.tx.save(update_fields=["status", "is_hold"])

        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_reject(user=self.recipient, tx_id=self.tx.id)

    def test_accept_requires_p2p(self):
        non_p2p = Transaction.objects.create(
            tx_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=None,
            to_wallet=self.recipient_wallet,
        )

        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_accept(user=self.recipient, tx_id=non_p2p.id)

    def test_reject_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            MoneyFlowService.p2p_reject(user=self.sender, tx_id=self.tx.id)

    def test_accept_reject_missing_destination_wallet(self):
        fake_tx = SimpleNamespace(
            tx_type=TransactionType.P2P,
            status=TransactionStatus.PENDING,
            is_hold=True,
            to_wallet_id=None,
        )

        with mock.patch(
            "transactions.services.Transaction.objects.select_for_update"
        ) as mocked_select:
            mocked_select.return_value.get.return_value = fake_tx
            with self.assertRaises(ValidationError):
                MoneyFlowService.p2p_accept(
                    user=self.recipient, tx_id="tx_missing_wallet"
                )

    def test_accept_reject_inactive_wallets(self):
        fake_tx = SimpleNamespace(
            tx_type=TransactionType.P2P,
            status=TransactionStatus.PENDING,
            is_hold=True,
            to_wallet_id=2,
            from_wallet_id=1,
            amount=Decimal("5.00"),
            to_wallet=SimpleNamespace(user_id=self.recipient.id),
        )
        from_wallet = SimpleNamespace(
            id=1, status=WalletStatus.SUSPENDED, held_balance=Decimal("10.00")
        )
        to_wallet = SimpleNamespace(id=2, status=WalletStatus.ACTIVE)

        with mock.patch(
            "transactions.services.Transaction.objects.select_for_update"
        ) as mocked_tx_select, mock.patch(
            "transactions.services.Wallet.objects.select_for_update"
        ) as mocked_wallet_select:
            mocked_tx_select.return_value.get.return_value = fake_tx
            mocked_wallet_select.return_value.filter.return_value = [
                from_wallet,
                to_wallet,
            ]
            with self.assertRaises(ValidationError):
                MoneyFlowService.p2p_accept(
                    user=self.recipient, tx_id="tx_inactive_wallet"
                )

    def test_accept_reject_insufficient_held_balance(self):
        fake_tx = SimpleNamespace(
            tx_type=TransactionType.P2P,
            status=TransactionStatus.PENDING,
            is_hold=True,
            to_wallet_id=2,
            from_wallet_id=1,
            amount=Decimal("50.00"),
            to_wallet=SimpleNamespace(user_id=self.recipient.id),
        )
        from_wallet = SimpleNamespace(
            id=1, status=WalletStatus.ACTIVE, held_balance=Decimal("10.00")
        )
        to_wallet = SimpleNamespace(id=2, status=WalletStatus.ACTIVE)

        with mock.patch(
            "transactions.services.Transaction.objects.select_for_update"
        ) as mocked_tx_select, mock.patch(
            "transactions.services.Wallet.objects.select_for_update"
        ) as mocked_wallet_select:
            mocked_tx_select.return_value.get.return_value = fake_tx
            mocked_wallet_select.return_value.filter.return_value = [
                from_wallet,
                to_wallet,
            ]
            with self.assertRaises(ValidationError):
                MoneyFlowService.p2p_accept(
                    user=self.recipient, tx_id="tx_low_hold_accept"
                )
            with self.assertRaises(ValidationError):
                MoneyFlowService.p2p_reject(
                    user=self.recipient, tx_id="tx_low_hold_reject"
                )

    def test_accept_reject_inactive_recipient_wallet(self):
        self.recipient_wallet.status = WalletStatus.SUSPENDED
        self.recipient_wallet.save(update_fields=["status"])

        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_accept(user=self.recipient, tx_id=self.tx.id)

    def test_accept_reject_inactive_sender_wallet(self):
        self.sender_wallet.status = WalletStatus.SUSPENDED
        self.sender_wallet.save(update_fields=["status"])

        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_accept(user=self.recipient, tx_id=self.tx.id)

    def test_accept_reject_insufficient_held_balance_real(self):
        self.sender_wallet.held_balance = Decimal("0.00")
        self.sender_wallet.save(update_fields=["held_balance"])

        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_accept(user=self.recipient, tx_id=self.tx.id)
        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_reject(user=self.recipient, tx_id=self.tx.id)
