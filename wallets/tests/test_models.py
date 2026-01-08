from django.test import TestCase

from shared.tests.factories import create_wallet


class WalletModelTests(TestCase):
    def test_wallet_str(self):
        wallet = create_wallet()
        self.assertEqual(str(wallet), f"{wallet.user.id}:{wallet.name}")
