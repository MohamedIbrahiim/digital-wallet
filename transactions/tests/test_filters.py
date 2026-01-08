from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from shared.tests.factories import create_user, create_wallet
from transactions.filters import TransactionFilter
from transactions.models import Transaction, TransactionType, TransactionStatus


class TransactionFilterTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = create_user()
        self.other_user = create_user()
        self.wallet = create_wallet(user=self.user, balance=Decimal("100.00"))
        self.other_wallet = create_wallet(
            user=self.other_user, balance=Decimal("10.00")
        )

        Transaction.objects.create(
            tx_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("5.00"),
            from_wallet=None,
            to_wallet=self.wallet,
        )
        Transaction.objects.create(
            tx_type=TransactionType.INTERNAL,
            status=TransactionStatus.COMPLETED,
            amount=Decimal("2.00"),
            from_wallet=self.wallet,
            to_wallet=self.wallet,
        )

    def test_filter_direction_deposit(self):
        request = self.factory.get("/transactions/?direction=deposit")
        request.user = self.user
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"direction": "deposit"},
        )
        self.assertEqual(f.qs.count(), 1)

    def test_filter_direction_outgoing(self):
        request = self.factory.get("/transactions/?direction=outgoing")
        request.user = self.user
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"direction": "outgoing"},
        )
        self.assertEqual(f.qs.count(), 1)

    def test_filter_direction_incoming(self):
        request = self.factory.get("/transactions/?direction=incoming")
        request.user = self.user
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"direction": "incoming"},
        )
        self.assertEqual(f.qs.count(), 1)

    def test_filter_direction_internal(self):
        request = self.factory.get("/transactions/?direction=internal")
        request.user = self.user
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"direction": "internal"},
        )
        self.assertEqual(f.qs.count(), 1)

    def test_filter_direction_unknown_value(self):
        request = self.factory.get("/transactions/?direction=unknown")
        request.user = self.user
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"direction": "unknown"},
        )
        self.assertEqual(f.qs.count(), 2)

    def test_filter_direction_unknown_value_direct(self):
        request = self.factory.get("/transactions/?direction=unknown")
        request.user = self.user
        f = TransactionFilter(
            request=request, queryset=Transaction.objects.all(), data={}
        )
        qs = f.filter_direction(Transaction.objects.all(), "direction", "unknown")
        self.assertEqual(qs.count(), 2)

    def test_filter_direction_requires_auth(self):
        request = self.factory.get("/transactions/?direction=outgoing")
        request.user = None
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"direction": "outgoing"},
        )
        self.assertEqual(f.qs.count(), 0)

    def test_filter_wallet_tag_valid(self):
        request = self.factory.get(
            f"/transactions/?wallet_tag={self.wallet.reference_tag}"
        )
        request.user = self.user
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"wallet_tag": self.wallet.reference_tag},
        )
        self.assertEqual(f.qs.count(), 2)

    def test_filter_wallet_tag_invalid(self):
        request = self.factory.get("/transactions/?wallet_tag=@wlt_missing.999")
        request.user = self.user
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"wallet_tag": "@wlt_missing.999"},
        )
        with self.assertRaises(ValidationError):
            _ = list(f.qs)

    def test_filter_wallet_tag_empty(self):
        request = self.factory.get("/transactions/?wallet_tag=")
        request.user = self.user
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"wallet_tag": ""},
        )
        self.assertEqual(f.qs.count(), 2)

    def test_filter_wallet_tag_empty_direct(self):
        request = self.factory.get("/transactions/?wallet_tag=")
        request.user = self.user
        f = TransactionFilter(
            request=request, queryset=Transaction.objects.all(), data={}
        )
        qs = f.filter_wallet_tag(Transaction.objects.all(), "wallet_tag", "")
        self.assertEqual(qs.count(), 2)

    def test_filter_wallet_tag_requires_auth(self):
        request = self.factory.get(
            f"/transactions/?wallet_tag={self.wallet.reference_tag}"
        )
        request.user = None
        f = TransactionFilter(
            request=request,
            queryset=Transaction.objects.all(),
            data={"wallet_tag": self.wallet.reference_tag},
        )
        self.assertEqual(f.qs.count(), 0)
