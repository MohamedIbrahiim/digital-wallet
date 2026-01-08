from decimal import Decimal

from django.test import TestCase

from shared.tests.factories import create_user, create_wallet
from transactions.models import Transaction, TransactionType, TransactionStatus
from transactions.serializers import TransactionSerializer, TransactionHistorySerializer


class TransactionSerializerTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.other_user = create_user()
        self.wallet = create_wallet(user=self.user)
        self.other_wallet = create_wallet(user=self.other_user)

    def test_transaction_serializer_includes_wallet_tags(self):
        tx = Transaction.objects.create(
            tx_type=TransactionType.P2P,
            status=TransactionStatus.PENDING,
            amount=Decimal("5.00"),
            from_wallet=self.wallet,
            to_wallet=self.other_wallet,
        )

        data = TransactionSerializer(tx).data

        self.assertEqual(data["from_wallet"], self.wallet.id)
        self.assertEqual(data["to_wallet"], self.other_wallet.id)
        self.assertEqual(data["from_wallet_tag"], self.wallet.reference_tag)
        self.assertEqual(data["to_wallet_tag"], self.other_wallet.reference_tag)

    def test_transaction_serializer_meta_fields(self):
        self.assertIn("id", TransactionSerializer.Meta.fields)
        self.assertIn("from_wallet_tag", TransactionSerializer.Meta.fields)
        self.assertEqual(
            TransactionSerializer.Meta.read_only_fields,
            TransactionSerializer.Meta.fields,
        )

    def test_history_serializer_source_transfer_format(self):
        tx = Transaction.objects.create(
            tx_type=TransactionType.INTERNAL,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=self.wallet,
            to_wallet=self.wallet,
        )

        data = TransactionHistorySerializer(tx, context={}).data

        self.assertIn(self.wallet.reference_tag, data["source"])
        self.assertIn("direction_label", TransactionHistorySerializer.Meta.fields)

    def test_history_serializer_unknown_source(self):
        tx = Transaction(
            tx_type=TransactionType.INTERNAL,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=None,
            to_wallet=None,
        )

        data = TransactionHistorySerializer(tx, context={}).data

        self.assertEqual(data["source"], "Unknown")

    def test_history_serializer_direction_labels(self):
        tx = Transaction.objects.create(
            tx_type=TransactionType.P2P,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=self.wallet,
            to_wallet=self.other_wallet,
        )

        data = TransactionHistorySerializer(tx, context={}).data
        self.assertEqual(data["direction"], "unknown")
        self.assertEqual(data["direction_label"], "Unknown")
