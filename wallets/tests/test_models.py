from django.test import TestCase

from shared.tests.factories import create_wallet
from wallets.models import Wallet
from unittest import mock


class WalletModelTests(TestCase):
    def test_wallet_str(self):
        wallet = create_wallet()
        self.assertEqual(str(wallet), f"{wallet.user.id}:{wallet.name}")

    def test_reference_tag_generation_avoids_collision(self):
        existing = create_wallet(reference_tag="@wlt_dup.1")
        user = existing.user

        with mock.patch(
            "wallets.models.generate_wallet_reference_tag",
            side_effect=["@wlt_dup.1", "@wlt_new.2"],
        ):
            wallet = Wallet.objects.create(
                user=user, name="Second", wallet_type="current"
            )

        self.assertEqual(wallet.reference_tag, "@wlt_new.2")
