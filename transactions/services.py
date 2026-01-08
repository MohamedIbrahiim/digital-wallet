from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError

from transactions.utils import (
    enforce_daily_outgoing_limit,
    enforce_per_transaction_limit,
)
from transactions.models import Transaction, TransactionStatus, TransactionType
from wallets.models import Wallet, WalletStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Limits:
    max_per_tx: Optional[Decimal] = None


def _validate_amount(amount: Decimal):
    if amount is None or amount <= 0:
        raise ValidationError({"amount": _("Amount must be greater than zero.")})


def _ensure_wallet_active(wallet: Wallet):
    if wallet.status != WalletStatus.ACTIVE:
        raise ValidationError({"wallet": _("Wallet is not active.")})


def _ensure_wallets_active(*wallets: Wallet):
    for wallet in wallets:
        _ensure_wallet_active(wallet)


def _lock_wallets_by_reference_tags(
    from_reference_tag: str, to_reference_tag: str
) -> tuple[Wallet, Wallet]:
    locked_wallets = Wallet.objects.select_for_update().filter(
        reference_tag__in=[from_reference_tag, to_reference_tag]
    )
    wallets_map = {w.reference_tag: w for w in locked_wallets}

    from_wallet = wallets_map.get(from_reference_tag)
    to_wallet = wallets_map.get(to_reference_tag)

    if not from_wallet or not to_wallet:
        raise ValidationError(_("One or more wallets do not exist."))

    return from_wallet, to_wallet


def _ensure_internal_ownership(user, from_wallet: Wallet, to_wallet: Wallet):
    if from_wallet.user.id != user.id or to_wallet.user.id != user.id:
        raise PermissionDenied(_("You can only transfer between your own wallets."))


def _ensure_p2p_ownership(user, from_wallet: Wallet):
    if from_wallet.user.id != user.id:
        raise PermissionDenied(_("You do not have permission to use this wallet."))


class MoneyFlowService:
    """
    All money mutations must go through this service.
    Ensures atomicity, locking, and correct balance/hold behavior.
    """

    @staticmethod
    @transaction.atomic
    def deposit(
        *,
        user,
        wallet_id: int,
        amount: Decimal,
        external_source: str = "",
        metadata: Optional[dict] = None,
    ) -> Transaction:
        logger.info(
            "deposit_service_start user_id=%s wallet_id=%s amount=%s",
            getattr(user, "pk", None),
            wallet_id,
            amount,
        )
        _validate_amount(amount)

        # Limits: per-tx (no daily outgoing limit for deposits)
        enforce_per_transaction_limit(tx_type=TransactionType.DEPOSIT, amount=amount)

        # Lock wallet row
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        if wallet.user.id != user.id:
            raise PermissionDenied(
                _("You do not have permission to access this wallet.")
            )
        _ensure_wallet_active(wallet)

        # Update balance
        wallet.balance = (wallet.balance or Decimal("0")) + amount
        wallet.save(update_fields=["balance", "updated_at"])

        tx = Transaction.objects.create(
            tx_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            amount=amount,
            from_wallet=None,
            to_wallet=wallet,
            external_source=external_source or "",
            metadata=metadata or {},
            is_hold=False,
            resolved_at=timezone.now(),
        )
        logger.info(
            "deposit_service_success user_id=%s wallet_id=%s tx_id=%s",
            getattr(user, "pk", None),
            wallet_id,
            tx.pk,
        )
        return tx

    @staticmethod
    @transaction.atomic
    def internal_transfer(
        *,
        user,
        from_reference_tag: str,
        to_reference_tag: str,
        amount: Decimal,
        metadata: Optional[dict] = None,
    ) -> Transaction:
        logger.info(
            "internal_transfer_service_start user_id=%s from_reference_tag=%s to_reference_tag=%s amount=%s",
            getattr(user, "pk", None),
            from_reference_tag,
            to_reference_tag,
            amount,
        )
        _validate_amount(amount)

        if from_reference_tag == to_reference_tag:
            raise ValidationError(
                {"to_reference_tag": _("Destination reference tag must be different.")}
            )

        # Limits: per-tx
        enforce_per_transaction_limit(tx_type=TransactionType.INTERNAL, amount=amount)

        from_wallet, to_wallet = _lock_wallets_by_reference_tags(
            from_reference_tag, to_reference_tag
        )
        _ensure_internal_ownership(user, from_wallet, to_wallet)

        _ensure_wallets_active(from_wallet, to_wallet)

        # Limits: daily outgoing (apply after locking wallets)
        enforce_daily_outgoing_limit(
            wallet_id=from_wallet.id,
            tx_type=TransactionType.INTERNAL,
            amount=amount,
        )

        if from_wallet.balance < amount:
            raise ValidationError({"amount": _("Insufficient funds.")})

        from_wallet.balance -= amount
        to_wallet.balance += amount

        from_wallet.save(update_fields=["balance", "updated_at"])
        to_wallet.save(update_fields=["balance", "updated_at"])

        tx = Transaction.objects.create(
            tx_type=TransactionType.INTERNAL,
            status=TransactionStatus.COMPLETED,
            amount=amount,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            metadata=metadata or {},
            is_hold=False,
            resolved_at=timezone.now(),
        )
        logger.info(
            "internal_transfer_service_success user_id=%s tx_id=%s",
            getattr(user, "pk", None),
            tx.pk,
        )
        return tx

    @staticmethod
    @transaction.atomic
    def p2p_send_hold(
        *,
        user,
        from_reference_tag: str,
        to_reference_tag: str,
        amount: Decimal,
        metadata: Optional[dict] = None,
    ) -> Transaction:
        logger.info(
            "p2p_send_service_start user_id=%s from_reference_tag=%s to_reference_tag=%s amount=%s",
            getattr(user, "pk", None),
            from_reference_tag,
            to_reference_tag,
            amount,
        )
        """
        P2P send that creates a PENDING transaction and holds funds on sender:
        - sender.balance decreases
        - sender.held_balance increases
        - receiver isn't credited until acceptance
        """
        _validate_amount(amount)

        if from_reference_tag == to_reference_tag:
            raise ValidationError(
                {"to_reference_tag": _("Destination reference tag must be different.")}
            )

        # Limits: per-tx
        enforce_per_transaction_limit(tx_type=TransactionType.P2P, amount=amount)

        from_wallet, to_wallet = _lock_wallets_by_reference_tags(
            from_reference_tag, to_reference_tag
        )
        _ensure_p2p_ownership(user, from_wallet)

        _ensure_wallets_active(from_wallet, to_wallet)

        # Limits: daily outgoing (apply after locking wallets)
        enforce_daily_outgoing_limit(
            wallet_id=from_wallet.id,
            tx_type=TransactionType.P2P,
            amount=amount,
        )

        if from_wallet.balance < amount:
            raise ValidationError({"amount": _("Insufficient funds.")})

        # Hold funds
        from_wallet.balance -= amount
        from_wallet.held_balance += amount
        from_wallet.save(update_fields=["balance", "held_balance", "updated_at"])

        tx = Transaction.objects.create(
            tx_type=TransactionType.P2P,
            status=TransactionStatus.PENDING,
            amount=amount,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            metadata=metadata or {},
            is_hold=True,
            held_at=timezone.now(),
        )
        logger.info(
            "p2p_send_service_success user_id=%s tx_id=%s",
            getattr(user, "pk", None),
            tx.pk,
        )
        return tx

    @staticmethod
    @transaction.atomic
    def p2p_accept(*, user, tx_id: str) -> Transaction:
        """
        Recipient accepts a pending P2P transaction:
        - release sender hold
        - credit recipient wallet
        - mark tx completed
        """
        tx, from_wallet, to_wallet = MoneyFlowService._lock_and_validate_p2p(
            user=user, tx_id=tx_id, action="accept"
        )

        # Apply movements
        from_wallet.held_balance -= tx.amount
        to_wallet.balance += tx.amount

        from_wallet.save(update_fields=["held_balance", "updated_at"])
        to_wallet.save(update_fields=["balance", "updated_at"])

        # Mark tx resolved
        tx.status = TransactionStatus.COMPLETED
        tx.is_hold = False
        tx.resolved_at = timezone.now()
        tx.save(update_fields=["status", "is_hold", "resolved_at", "updated_at"])

        logger.info(
            "p2p_accept_service_success user_id=%s tx_id=%s",
            getattr(user, "pk", None),
            tx.pk,
        )
        return tx

    @staticmethod
    @transaction.atomic
    def p2p_reject(*, user, tx_id: str) -> Transaction:
        """
        Recipient rejects a pending P2P transaction:
        - release sender hold back to sender balance
        - mark tx rejected
        """
        tx, from_wallet, _to_wallet = MoneyFlowService._lock_and_validate_p2p(
            user=user, tx_id=tx_id, action="reject"
        )

        # Release hold back to sender
        from_wallet.held_balance -= tx.amount
        from_wallet.balance += tx.amount
        from_wallet.save(update_fields=["held_balance", "balance", "updated_at"])

        tx.status = TransactionStatus.REJECTED
        tx.is_hold = False
        tx.resolved_at = timezone.now()
        tx.save(update_fields=["status", "is_hold", "resolved_at", "updated_at"])

        logger.info(
            "p2p_reject_service_success user_id=%s tx_id=%s",
            getattr(user, "pk", None),
            tx.pk,
        )
        return tx

    @staticmethod
    def _lock_and_validate_p2p(
        *, user, tx_id: str, action: str
    ) -> tuple[Transaction, Wallet, Wallet]:
        logger.info(
            "p2p_action_validate_start user_id=%s tx_id=%s action=%s",
            getattr(user, "pk", None),
            tx_id,
            action,
        )
        tx = Transaction.objects.select_for_update().get(id=tx_id)

        if tx.tx_type != TransactionType.P2P:
            raise ValidationError(
                {"transaction": _("Only P2P transactions can be accepted or rejected.")}
            )

        if tx.status != TransactionStatus.PENDING or not tx.is_hold:
            raise ValidationError({"transaction": _("Transaction is not pending.")})

        if not tx.to_wallet_id:
            raise ValidationError(
                {"transaction": _("Transaction has no destination wallet.")}
            )

        if tx.to_wallet.user_id != user.id:
            if action == "accept":
                raise PermissionDenied(
                    _("You do not have permission to accept this transaction.")
                )
            raise PermissionDenied(
                _("You do not have permission to reject this transaction.")
            )

        wallet_ids = sorted([tx.from_wallet_id, tx.to_wallet_id])
        wallets = Wallet.objects.select_for_update().filter(id__in=wallet_ids)
        wallets_map = {w.id: w for w in wallets}

        from_wallet = wallets_map[tx.from_wallet_id]
        to_wallet = wallets_map[tx.to_wallet_id]

        if from_wallet.status != WalletStatus.ACTIVE:
            raise ValidationError({"wallet": _("Sender wallet is not active.")})
        if to_wallet.status != WalletStatus.ACTIVE:
            raise ValidationError({"wallet": _("Recipient wallet is not active.")})

        if from_wallet.held_balance < tx.amount:
            if action == "accept":
                raise ValidationError(
                    {
                        "transaction": _(
                            "Insufficient held balance to complete transaction."
                        )
                    }
                )
            raise ValidationError(
                {"transaction": _("Insufficient held balance to release transaction.")}
            )

        return tx, from_wallet, to_wallet
