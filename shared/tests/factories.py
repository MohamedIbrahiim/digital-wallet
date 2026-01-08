from itertools import count

from django.contrib.auth import get_user_model

from wallets.models import Wallet

User = get_user_model()

_user_counter = count(800)
_wallet_counter = count(1)


def create_user(**kwargs):
    number = next(_user_counter)
    defaults = {
        "mobile_number": f"+201234567{number:03d}",
        "password": "123456",
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def create_superuser(**kwargs):
    number = next(_user_counter)
    defaults = {
        "mobile_number": f"+201234567{number:03d}",
        "password": "123456",
    }
    defaults.update(kwargs)
    return User.objects.create_superuser(**defaults)


def create_wallet(user=None, **kwargs):
    if user is None:
        user = create_user()
    number = next(_wallet_counter)
    defaults = {
        "user": user,
        "name": f"Wallet {number}",
    }
    defaults.update(kwargs)
    return Wallet.objects.create(**defaults)
