import secrets
import string


def _random_suffix(length: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_wallet_reference_tag(wallet_id: int) -> str:
    return f"@wlt_{_random_suffix()}.{wallet_id}"
