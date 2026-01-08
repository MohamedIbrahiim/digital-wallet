from itertools import count

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from wallets.models import Wallet
from users.models import UserAccessToken

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


def create_access_token_record(*, user, jti: str, expires_in_seconds: int = 120):
    expires_at = timezone.now() + timedelta(seconds=expires_in_seconds)
    return UserAccessToken.touch(user=user, jti=jti, expires_at=expires_at)
