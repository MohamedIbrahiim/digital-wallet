from __future__ import annotations

import logging

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from wallets.models import Wallet

logger = logging.getLogger(__name__)


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = (
            "id",
            "name",
            "wallet_type",
            "balance",
            "status",
            "reference_tag",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "balance",
            "status",
            "reference_tag",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        """
        Enforce uniqueness per user at API level for a cleaner error message.
        DB constraint will still protect us.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        name = (attrs.get("name") or "").strip()
        if user and user.is_authenticated and name:
            if Wallet.objects.filter(user=user, name__iexact=name).exists():
                logger.info(
                    "wallet_name_conflict user_id=%s name=%s",
                    user.pk,
                    name,
                )
                raise serializers.ValidationError(
                    {"name": _("You already have a wallet with this name.")}
                )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["user"] = request.user

        wallet = super().create(validated_data)
        logger.info(
            "wallet_created user_id=%s wallet_id=%s name=%s",
            wallet.user_id,
            wallet.pk,
            wallet.name,
        )
        return wallet
