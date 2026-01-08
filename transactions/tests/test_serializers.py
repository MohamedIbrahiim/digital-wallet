from django.test import SimpleTestCase
from rest_framework import serializers

from transactions.serializers import DepositSerializer, BaseWalletTransferSerializer


class TransactionSerializerTests(SimpleTestCase):
    def test_deposit_rejects_non_positive_amount(self):
        serializer = DepositSerializer(data={"amount": "0.00"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_transfer_requires_source_tag(self):
        serializer = BaseWalletTransferSerializer(
            data={
                "from_reference_tag": "   ",
                "to_reference_tag": "@wlt_bbbb.2",
                "amount": "1.00",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("from_reference_tag", serializer.errors)

    def test_transfer_requires_destination_tag(self):
        serializer = BaseWalletTransferSerializer(
            data={
                "from_reference_tag": "@wlt_bbbb.2",
                "to_reference_tag": "   ",
                "amount": "1.00",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("to_reference_tag", serializer.errors)

    def test_transfer_rejects_same_reference_tag(self):
        serializer = BaseWalletTransferSerializer(
            data={
                "from_reference_tag": "@wlt_aaaa.1",
                "to_reference_tag": "@wlt_aaaa.1",
                "amount": "1.00",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("to_reference_tag", serializer.errors)

    def test_validate_requires_source_tag(self):
        serializer = BaseWalletTransferSerializer()
        with self.assertRaises(serializers.ValidationError):
            serializer.validate(
                {
                    "from_reference_tag": "",
                    "to_reference_tag": "@wlt_bbbb.2",
                    "amount": "1.00",
                }
            )

    def test_validate_requires_destination_tag(self):
        serializer = BaseWalletTransferSerializer()
        with self.assertRaises(serializers.ValidationError):
            serializer.validate(
                {
                    "from_reference_tag": "@wlt_bbbb.2",
                    "to_reference_tag": "",
                    "amount": "1.00",
                }
            )
