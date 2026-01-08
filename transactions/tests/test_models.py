from decimal import Decimal

from django.test import TestCase

from shared.tests.factories import create_wallet
from transactions.models import Transaction, TransactionType, TransactionStatus


class TransactionModelTests(TestCase):
    def test_transaction_str(self):
        wallet = create_wallet()
        tx = Transaction.objects.create(
            tx_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("10.00"),
            from_wallet=None,
            to_wallet=wallet,
        )

        self.assertEqual(str(tx), f"{tx.tx_type}:{tx.amount}:{tx.status}")
