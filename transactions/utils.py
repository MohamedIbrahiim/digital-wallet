import ulid
from decimal import Decimal
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError


def _get_limits_for(tx_type: str) -> dict:
    from transactions.models import TransactionType

    cfg = getattr(settings, "WALLET_LIMITS", {}) or {}
    defaults = cfg.get("DEFAULT", {}) or {}

    # Map tx_type -> key
    key = {
        str(TransactionType.P2P): "P2P",
        str(TransactionType.INTERNAL): "INTERNAL",
        str(TransactionType.DEPOSIT): "DEPOSIT",
    }.get(tx_type, None)

    specific = cfg.get(key, {}) if key else {}
    merged = {**defaults, **specific}

    def _to_decimal(value):
        if value is None:
            return None
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    for field in ("MAX_PER_TRANSACTION", "DAILY_WALLET_OUTGOING_LIMIT"):
        if field in merged:
            merged[field] = _to_decimal(merged[field])

    return merged


def enforce_per_transaction_limit(*, tx_type: str, amount: Decimal) -> None:
    limits = _get_limits_for(tx_type)
    max_per_tx = limits.get("MAX_PER_TRANSACTION")

    if max_per_tx is not None and amount > max_per_tx:
        raise ValidationError({"amount": _("Amount exceeds per-transaction limit.")})


def enforce_daily_outgoing_limit(
    *, wallet_id: int, tx_type: str, amount: Decimal
) -> None:
    """
    Applies to outgoing flows where money leaves a wallet or is reserved from it.
    We count:
      - INTERNAL transfers (from_wallet)
      - P2P sends (from_wallet)
    We do NOT count deposits.
    """
    from transactions.models import Transaction, TransactionStatus, TransactionType

    if tx_type == TransactionType.DEPOSIT:
        return

    limits = _get_limits_for(tx_type)
    daily_limit = limits.get("DAILY_WALLET_OUTGOING_LIMIT")
    if daily_limit is None:
        return

    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_today = Transaction.objects.filter(
        from_wallet_id=wallet_id,
        created_at__gte=start,
        status__in=[TransactionStatus.COMPLETED],
        tx_type__in=[TransactionType.INTERNAL, TransactionType.P2P],
    ).aggregate(total=Sum("amount")).get("total") or Decimal("0.00")

    if total_today + amount > daily_limit:
        raise ValidationError({"amount": _("Daily wallet limit exceeded.")})


def generate_ulid():
    return ulid.new().str
