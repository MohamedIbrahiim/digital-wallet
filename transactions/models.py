from decimal import Decimal
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from transactions.choices import TransactionType, TransactionStatus
from transactions.utils import generate_ulid
from wallets.models import Wallet


class Transaction(models.Model):
    """
    High-level transaction record.

    - For DEPOSIT: to_wallet is required, from_wallet is null.
    - For INTERNAL: both from_wallet and to_wallet required (same user enforced in service).
    - For P2P: both required. Usually starts PENDING with hold on from_wallet.
    """

    id = models.CharField(
        primary_key=True,
        max_length=26,
        default=generate_ulid,
        editable=False,
    )

    tx_type = models.CharField(
        max_length=20,
        choices=TransactionType,
        verbose_name=_("Transaction type"),
    )

    status = models.CharField(
        max_length=20,
        choices=TransactionStatus,
        default=TransactionStatus.COMPLETED,
        verbose_name=_("Status"),
    )

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Amount"),
    )

    # who pays (nullable for deposit)
    from_wallet = models.ForeignKey(
        Wallet,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="outgoing_transactions",
        verbose_name=_("From wallet"),
    )

    to_wallet = models.ForeignKey(
        Wallet,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="incoming_transactions",
        verbose_name=_("To wallet"),
    )

    external_source = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("External source"),
        help_text=_("Used for deposits (e.g., bank, card, cash, promo)."),
    )

    metadata = models.JSONField(
        blank=True,
        default=dict,
        verbose_name=_("Metadata"),
        help_text=_("Extra transaction details (optional)."),
    )

    is_hold = models.BooleanField(
        default=False,
        verbose_name=_("Is hold"),
        help_text=_("True if amount is reserved until approval (P2P pending)."),
    )

    held_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Held at"),
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Resolved at"),
        help_text=_("When transaction moved from pending to completed/rejected."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        indexes = [
            models.Index(fields=["from_wallet", "-created_at"]),
            models.Index(fields=["to_wallet", "-created_at"]),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="tx_amount_positive",
            ),
            # Deposit: must have to_wallet
            models.CheckConstraint(
                condition=~Q(tx_type=TransactionType.DEPOSIT)
                | Q(to_wallet__isnull=False),
                name="deposit_requires_to_wallet",
            ),
            # Internal: must have both wallets
            models.CheckConstraint(
                condition=~Q(tx_type=TransactionType.INTERNAL)
                | (Q(from_wallet__isnull=False) & Q(to_wallet__isnull=False)),
                name="internal_requires_both_wallets",
            ),
            # P2P: must have both wallets
            models.CheckConstraint(
                condition=~Q(tx_type=TransactionType.P2P)
                | (Q(from_wallet__isnull=False) & Q(to_wallet__isnull=False)),
                name="p2p_requires_both_wallets",
            ),
            # Hold must be pending (basic guard)
            models.CheckConstraint(
                condition=Q(is_hold=False) | Q(status=TransactionStatus.PENDING),
                name="hold_must_be_pending",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.tx_type}:{self.amount}:{self.status}"
