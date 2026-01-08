from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from wallets.choices import WalletType, WalletStatus
from wallets.utils import generate_wallet_reference_tag


class Wallet(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallets",
        db_index=True,
    )

    # Category/type (not unique)
    wallet_type = models.CharField(
        max_length=20,
        choices=WalletType,
        default=WalletType.CURRENT,
        verbose_name=_("Wallet type"),
    )

    # User-facing name (unique per user)
    name = models.CharField(
        max_length=100,
        verbose_name=_("Wallet name"),
        help_text=_("Unique wallet name per user (e.g., My Savings, Travel Fund)."),
    )

    reference_tag = models.CharField(
        max_length=40,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        verbose_name=_("Wallet reference tag"),
        help_text=_("Public wallet reference tag for transfers (e.g., @wlt_x7k9f.42)."),
    )

    balance = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Balance"),
    )

    held_balance = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Balance"),
    )

    status = models.CharField(
        max_length=20,
        choices=WalletStatus,
        default=WalletStatus.ACTIVE,
        verbose_name=_("Status"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Wallet")
        verbose_name_plural = _("Wallets")
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "user",
                name="uniq_wallet_name_per_user_ci",
            ),
            models.CheckConstraint(
                condition=Q(balance__gte=0),
                name="wallet_balance_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(held_balance__gte=0),
                name="wallet_held_balance_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "wallet_type"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.id}:{self.name}"

    def save(self, *args, **kwargs):
        if not self.reference_tag:
            super().save(*args, **kwargs)
            reference_tag = generate_wallet_reference_tag(self.pk)
            while Wallet.objects.filter(reference_tag=reference_tag).exists():
                reference_tag = generate_wallet_reference_tag(self.pk)
            Wallet.objects.filter(pk=self.pk).update(reference_tag=reference_tag)
            self.reference_tag = reference_tag
            return
        super().save(*args, **kwargs)
