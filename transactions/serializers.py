from decimal import Decimal
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from transactions.choices import (
    TransactionType,
    TransactionDirectionChoices,
)
from transactions.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    from_wallet_tag = serializers.CharField(
        source="from_wallet.reference_tag", read_only=True
    )
    to_wallet_tag = serializers.CharField(
        source="to_wallet.reference_tag", read_only=True
    )

    class Meta:
        model = Transaction
        fields = (
            "id",
            "tx_type",
            "status",
            "amount",
            "from_wallet",
            "from_wallet_tag",
            "to_wallet",
            "to_wallet_tag",
            "external_source",
            "metadata",
            "is_hold",
            "held_at",
            "resolved_at",
            "created_at",
        )
        read_only_fields = fields


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    external_source = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)

    def validate_amount(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero."))
        return value


class BaseWalletTransferSerializer(serializers.Serializer):
    from_reference_tag = serializers.CharField()
    to_reference_tag = serializers.CharField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    metadata = serializers.JSONField(required=False)

    def validate(self, attrs):
        from_tag = (attrs.get("from_reference_tag") or "").strip()
        to_tag = (attrs.get("to_reference_tag") or "").strip()
        if not from_tag:
            raise serializers.ValidationError(
                {"from_reference_tag": _("Source reference tag is required.")}
            )
        if not to_tag:
            raise serializers.ValidationError(
                {"to_reference_tag": _("Destination reference tag is required.")}
            )
        if from_tag == to_tag:
            raise serializers.ValidationError(
                {"to_reference_tag": _("Destination reference tag must be different.")}
            )
        return attrs


class TransactionHistorySerializer(serializers.ModelSerializer):
    direction = serializers.SerializerMethodField()
    direction_label = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    from_wallet_tag = serializers.CharField(
        source="from_wallet.reference_tag", read_only=True
    )
    to_wallet_tag = serializers.CharField(
        source="to_wallet.reference_tag", read_only=True
    )

    class Meta:
        model = Transaction
        fields = (
            "id",
            "tx_type",
            "status",
            "amount",
            "from_wallet_tag",
            "to_wallet_tag",
            "external_source",
            "is_hold",
            "held_at",
            "resolved_at",
            "created_at",
            "direction",
            "direction_label",
            "source",
        )

    def get_direction(self, obj: Transaction) -> str:
        """
        Direction relative to current user context:
        - deposit: money came from an external source into the user's wallet
        - outgoing: user sent money to someone else / another wallet
        - incoming: user received money from someone else
        - internal: transfer between user's wallets
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        # a deposit is always "deposit"
        if obj.tx_type == TransactionType.DEPOSIT:
            return "deposit"

        from_user_id = obj.from_wallet.user_id if obj.from_wallet else None
        to_user_id = obj.to_wallet.user_id if obj.to_wallet else None

        if user and user.is_authenticated:
            # internal transfer (both wallets belong to the user)
            if from_user_id == user.id and to_user_id == user.id:
                return "internal"
            if from_user_id == user.id:
                return "outgoing"
            if to_user_id == user.id:
                return "incoming"

        return "unknown"

    def get_source(self, obj: Transaction) -> str:
        """
        Human-readable source for UI:
        - for deposits: external_source
        - for transfers: wallet name and direction
        """
        if obj.tx_type == TransactionType.DEPOSIT:
            return obj.external_source or _("External")

        if obj.from_wallet and obj.to_wallet:
            return format_lazy(
                _("Transfer from {from_name} ({from_tag}) to {to_name} ({to_tag})"),
                from_name=obj.from_wallet.name,
                from_tag=obj.from_wallet.reference_tag,
                to_name=obj.to_wallet.name,
                to_tag=obj.to_wallet.reference_tag,
            )

        if obj.from_wallet:
            return format_lazy(
                _("From {from_name} ({from_tag})"),
                from_name=obj.from_wallet.name,
                from_tag=obj.from_wallet.reference_tag,
            )

        return str(_("Unknown"))

    def get_direction_label(self, obj: Transaction) -> str:
        direction = self.get_direction(obj)
        labels = {
            str(TransactionDirectionChoices.DEPOSIT): _("Deposit"),
            str(TransactionDirectionChoices.INCOMING): _("Incoming"),
            str(TransactionDirectionChoices.OUTGOING): _("Outgoing"),
            str(TransactionDirectionChoices.INTERNAL): _("Internal"),
        }
        return labels.get(direction, str(_("Unknown")))


class TransactionActionSerializer(serializers.Serializer):
    is_accepted = serializers.BooleanField()
