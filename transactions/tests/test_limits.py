from decimal import Decimal

from django.test import TestCase, override_settings
from rest_framework.exceptions import ValidationError

from shared.tests.factories import create_user, create_wallet
from transactions.models import Transaction, TransactionType, TransactionStatus
from transactions.services import MoneyFlowService
from transactions.utils import enforce_daily_outgoing_limit


class TransactionLimitsTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.wallet = create_wallet(user=self.user, balance=Decimal("1000.00"))
        self.second_wallet = create_wallet(user=self.user, balance=Decimal("1000.00"))

    @override_settings(
        WALLET_LIMITS={
            "DEFAULT": {"MAX_PER_TRANSACTION": "100.00"},
            "INTERNAL": {"MAX_PER_TRANSACTION": "50.00"},
            "P2P": {"MAX_PER_TRANSACTION": "25.00"},
            "DEPOSIT": {"MAX_PER_TRANSACTION": "200.00"},
        }
    )
    def test_per_transaction_limits_enforced(self):
        with self.assertRaises(ValidationError):
            MoneyFlowService.internal_transfer(
                user=self.user,
                from_reference_tag=self.wallet.reference_tag,
                to_reference_tag=self.second_wallet.reference_tag,
                amount=Decimal("60.00"),
            )

        with self.assertRaises(ValidationError):
            MoneyFlowService.p2p_send_hold(
                user=self.user,
                from_reference_tag=self.wallet.reference_tag,
                to_reference_tag=self.second_wallet.reference_tag,
                amount=Decimal("30.00"),
            )

        with self.assertRaises(ValidationError):
            MoneyFlowService.deposit(
                user=self.user,
                wallet_id=self.wallet.id,
                amount=Decimal("300.00"),
            )

    @override_settings(
        WALLET_LIMITS={
            "DEFAULT": {
                "MAX_PER_TRANSACTION": None,
                "DAILY_WALLET_OUTGOING_LIMIT": None,
            },
            "INTERNAL": {},
            "P2P": {},
            "DEPOSIT": {},
        }
    )
    def test_limits_allow_none_values(self):
        # Ensure None values are normalized and do not raise.
        MoneyFlowService.deposit(
            user=self.user,
            wallet_id=self.wallet.id,
            amount=Decimal("10.00"),
        )

    def test_daily_limit_skips_for_deposit(self):
        enforce_daily_outgoing_limit(
            wallet_id=self.wallet.id,
            tx_type=TransactionType.DEPOSIT,
            amount=Decimal("10.00"),
        )

    @override_settings(
        WALLET_LIMITS={
            "INTERNAL": {},
        }
    )
    def test_daily_limit_noop_when_not_configured(self):
        MoneyFlowService.internal_transfer(
            user=self.user,
            from_reference_tag=self.wallet.reference_tag,
            to_reference_tag=self.second_wallet.reference_tag,
            amount=Decimal("10.00"),
        )

    @override_settings(
        WALLET_LIMITS={
            "INTERNAL": {"DAILY_WALLET_OUTGOING_LIMIT": "100.00"},
            "P2P": {"DAILY_WALLET_OUTGOING_LIMIT": "100.00"},
        }
    )
    def test_daily_limit_counts_only_completed(self):
        Transaction.objects.create(
            tx_type=TransactionType.INTERNAL,
            status=TransactionStatus.PENDING,
            amount=Decimal("90.00"),
            from_wallet=self.wallet,
            to_wallet=self.second_wallet,
        )

        # Pending does not count; this should pass
        MoneyFlowService.internal_transfer(
            user=self.user,
            from_reference_tag=self.wallet.reference_tag,
            to_reference_tag=self.second_wallet.reference_tag,
            amount=Decimal("20.00"),
        )

        # Completed tx should count
        Transaction.objects.create(
            tx_type=TransactionType.INTERNAL,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("90.00"),
            from_wallet=self.wallet,
            to_wallet=self.second_wallet,
        )

        with self.assertRaises(ValidationError):
            MoneyFlowService.internal_transfer(
                user=self.user,
                from_reference_tag=self.wallet.reference_tag,
                to_reference_tag=self.second_wallet.reference_tag,
                amount=Decimal("20.00"),
            )
