from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError
from transactions.choices import TransactionDirectionChoices, TransactionType
from transactions.models import Transaction
from wallets.models import Wallet
from django.utils.translation import gettext_lazy as _


class TransactionFilter(filters.FilterSet):
    tx_type = filters.CharFilter(field_name="tx_type", lookup_expr="exact")
    status = filters.CharFilter(field_name="status", lookup_expr="exact")
    date_from = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    direction = filters.ChoiceFilter(
        choices=TransactionDirectionChoices, method="filter_direction"
    )
    wallet_tag = filters.CharFilter(method="filter_wallet_tag")

    def filter_direction(self, queryset, _name, value):
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return queryset.none()

        value = (value or "").lower()

        if value == TransactionDirectionChoices.DEPOSIT:
            return queryset.filter(tx_type=TransactionType.DEPOSIT)

        if value == TransactionDirectionChoices.INCOMING:
            return queryset.filter(to_wallet__user=user).exclude(
                tx_type=TransactionType.DEPOSIT
            )

        if value == TransactionDirectionChoices.OUTGOING:
            return queryset.filter(from_wallet__user=user).exclude(
                tx_type=TransactionType.DEPOSIT
            )

        if value == TransactionDirectionChoices.INTERNAL:
            return queryset.filter(from_wallet__user=user, to_wallet__user=user)

        return queryset

    def filter_wallet_tag(self, queryset, _name, value):
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return queryset.none()

        value = (value or "").strip()
        if not value:
            return queryset

        wallet = (
            Wallet.objects.filter(reference_tag=value, user=user).only("id").first()
        )
        if not wallet:
            raise ValidationError({"wallet_tag": _("Wallet not found.")})

        return queryset.filter(Q(from_wallet=wallet) | Q(to_wallet=wallet))

    class Meta:
        model = Transaction
        fields = [
            "tx_type",
            "direction",
            "status",
            "date_from",
            "date_to",
            "wallet_tag",
        ]
