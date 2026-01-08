from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from shared.tests.factories import create_user, create_wallet
from transactions.models import Transaction, TransactionType, TransactionStatus
from transactions.serializers import TransactionHistorySerializer


class TransactionHistorySerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = create_user()
        self.other_user = create_user()
        self.wallet = create_wallet(user=self.user)
        self.second_wallet = create_wallet(user=self.user)
        self.other_wallet = create_wallet(user=self.other_user)

    def test_direction_and_source_for_deposit(self):
        tx = Transaction.objects.create(
            tx_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=None,
            to_wallet=self.wallet,
            external_source="bank",
        )

        request = self.factory.get("/transactions/")
        request.user = self.user
        serializer = TransactionHistorySerializer(
            instance=tx, context={"request": request}
        )

        self.assertEqual(serializer.data["direction"], "deposit")
        self.assertEqual(serializer.data["source"], "bank")

    def test_direction_and_source_for_internal(self):
        tx = Transaction.objects.create(
            tx_type=TransactionType.INTERNAL,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=self.wallet,
            to_wallet=self.second_wallet,
        )

        request = self.factory.get("/transactions/")
        request.user = self.user
        serializer = TransactionHistorySerializer(
            instance=tx, context={"request": request}
        )

        self.assertEqual(serializer.data["direction"], "internal")
        self.assertIn("wallet:", serializer.data["source"])

    def test_direction_outgoing_and_incoming(self):
        outgoing_tx = Transaction.objects.create(
            tx_type=TransactionType.P2P,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=self.wallet,
            to_wallet=self.other_wallet,
        )
        incoming_tx = Transaction.objects.create(
            tx_type=TransactionType.P2P,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=self.other_wallet,
            to_wallet=self.wallet,
        )

        request = self.factory.get("/transactions/")
        request.user = self.user

        outgoing = TransactionHistorySerializer(
            instance=outgoing_tx, context={"request": request}
        )
        incoming = TransactionHistorySerializer(
            instance=incoming_tx, context={"request": request}
        )

        self.assertEqual(outgoing.data["direction"], "outgoing")
        self.assertEqual(incoming.data["direction"], "incoming")

    def test_direction_unknown_without_user(self):
        tx = Transaction.objects.create(
            tx_type=TransactionType.P2P,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=self.wallet,
            to_wallet=self.other_wallet,
        )

        serializer = TransactionHistorySerializer(instance=tx, context={})
        self.assertEqual(serializer.data["direction"], "unknown")

    def test_source_from_wallet_only(self):
        tx = Transaction(
            tx_type=TransactionType.INTERNAL,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=self.wallet,
            to_wallet=None,
        )

        serializer = TransactionHistorySerializer(instance=tx, context={})
        self.assertTrue(serializer.data["source"].startswith("wallet:"))

    def test_source_unknown(self):
        tx = Transaction(
            tx_type=TransactionType.INTERNAL,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=None,
            to_wallet=None,
        )

        serializer = TransactionHistorySerializer(instance=tx, context={})
        self.assertEqual(serializer.data["source"], "unknown")
