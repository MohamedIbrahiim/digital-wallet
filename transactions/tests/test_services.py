from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError

from shared.tests.factories import create_user, create_wallet
from wallets.models import WalletStatus
from transactions.services import MoneyFlowService
from transactions.models import Transaction, TransactionType


class MoneyFlowServiceTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.other_user = create_user()
        self.wallet = create_wallet(user=self.user, balance=Decimal("100.00"))
        self.other_wallet = create_wallet(
            user=self.other_user, balance=Decimal("50.00")
        )
        self.second_wallet = create_wallet(user=self.user, balance=Decimal("10.00"))

    def test_deposit_increases_balance(self):
        tx = MoneyFlowService.deposit(
            user=self.user,
            wallet_id=self.wallet.id,
            amount=Decimal("25.00"),
        )
        self.wallet.refresh_from_db()

        self.assertEqual(self.wallet.balance, Decimal("125.00"))
        self.assertEqual(tx.tx_type, TransactionType.DEPOSIT)

    def test_deposit_rejects_wrong_owner(self):
        with self.assertRaises(PermissionDenied):
            MoneyFlowService.deposit(
                user=self.other_user,
                wallet_id=self.wallet.id,
                amount=Decimal("5.00"),
            )

    def test_deposit_rejects_invalid_amount(self):
        with self.assertRaises(ValidationError):
            MoneyFlowService.deposit(
                user=self.user,
                wallet_id=self.wallet.id,
                amount=Decimal("0.00"),
            )

    def test_deposit_rejects_inactive_wallet(self):
        self.wallet.status = WalletStatus.SUSPENDED
        self.wallet.save(update_fields=["status"])

        with self.assertRaises(ValidationError):
            MoneyFlowService.deposit(
                user=self.user,
                wallet_id=self.wallet.id,
                amount=Decimal("1.00"),
            )

    def test_internal_transfer_rejects_insufficient_funds(self):
        with self.assertRaises(ValidationError):
            MoneyFlowService.internal_transfer(
                user=self.user,
                from_reference_tag=self.second_wallet.reference_tag,
                to_reference_tag=self.wallet.reference_tag,
                amount=Decimal("500.00"),
            )

    def test_internal_transfer_rejects_same_wallet(self):
        with self.assertRaises(ValidationError):
            MoneyFlowService.internal_transfer(
                user=self.user,
                from_reference_tag=self.wallet.reference_tag,
                to_reference_tag=self.wallet.reference_tag,
                amount=Decimal("1.00"),
            )

    def test_internal_transfer_rejects_missing_wallet(self):
        with self.assertRaises(ValidationError):
            MoneyFlowService.internal_transfer(
                user=self.user,
                from_reference_tag="@wlt_missing.999",
                to_reference_tag=self.wallet.reference_tag,
                amount=Decimal("1.00"),
            )

    def test_internal_transfer_rejects_wrong_owner(self):
        with self.assertRaises(PermissionDenied):
            MoneyFlowService.internal_transfer(
                user=self.user,
                from_reference_tag=self.wallet.reference_tag,
                to_reference_tag=self.other_wallet.reference_tag,
                amount=Decimal("1.00"),
            )

    def test_p2p_send_hold_updates_balances(self):
        tx = MoneyFlowService.p2p_send_hold(
            user=self.user,
            from_reference_tag=self.wallet.reference_tag,
            to_reference_tag=self.other_wallet.reference_tag,
            amount=Decimal("20.00"),
        )
        self.wallet.refresh_from_db()

        self.assertEqual(self.wallet.balance, Decimal("80.00"))
        self.assertEqual(self.wallet.held_balance, Decimal("20.00"))
        self.assertTrue(tx.is_hold)
        self.assertEqual(tx.tx_type, TransactionType.P2P)

    def test_p2p_rejects_same_wallet(self):
        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_send_hold(
                user=self.user,
                from_reference_tag=self.wallet.reference_tag,
                to_reference_tag=self.wallet.reference_tag,
                amount=Decimal("1.00"),
            )

    def test_p2p_rejects_missing_wallet(self):
        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_send_hold(
                user=self.user,
                from_reference_tag="@wlt_missing.999",
                to_reference_tag=self.wallet.reference_tag,
                amount=Decimal("1.00"),
            )

    def test_p2p_rejects_wrong_owner(self):
        with self.assertRaises(PermissionDenied):
            MoneyFlowService.p2p_send_hold(
                user=self.user,
                from_reference_tag=self.other_wallet.reference_tag,
                to_reference_tag=self.wallet.reference_tag,
                amount=Decimal("1.00"),
            )

    def test_p2p_rejects_insufficient_funds(self):
        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_send_hold(
                user=self.user,
                from_reference_tag=self.second_wallet.reference_tag,
                to_reference_tag=self.other_wallet.reference_tag,
                amount=Decimal("100.00"),
            )

    def test_internal_transfer_creates_transaction(self):
        tx = MoneyFlowService.internal_transfer(
            user=self.user,
            from_reference_tag=self.wallet.reference_tag,
            to_reference_tag=self.second_wallet.reference_tag,
            amount=Decimal("10.00"),
        )

        self.assertIsNotNone(tx.pk)
        self.assertTrue(
            Transaction.objects.filter(
                pk=tx.pk, tx_type=TransactionType.INTERNAL
            ).exists()
        )
