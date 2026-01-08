import logging

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from transactions.filters import TransactionFilter
from transactions.models import Transaction
from transactions.serializers import (
    DepositSerializer,
    BaseWalletTransferSerializer,
    TransactionSerializer,
    TransactionHistorySerializer,
    TransactionActionSerializer,
)
from wallets.models import Wallet
from transactions.services import MoneyFlowService
from wallets.models import Wallet
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class WalletDepositView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DepositSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet = (
            Wallet.objects.filter(
                reference_tag=self.kwargs["reference_tag"], user=request.user
            )
            .only("id")
            .first()
        )
        if not wallet:
            raise ValidationError({"wallet": _("Wallet not found.")})

        logger.info(
            "deposit_attempt user_id=%s reference_tag=%s",
            request.user.pk,
            self.kwargs["reference_tag"],
        )
        tx = MoneyFlowService.deposit(
            user=request.user,
            wallet_id=wallet.id,
            amount=serializer.validated_data["amount"],
            external_source=serializer.validated_data.get("external_source", ""),
            metadata=serializer.validated_data.get("metadata", {}),
        )
        logger.info(
            "deposit_success user_id=%s reference_tag=%s tx_id=%s",
            request.user.pk,
            self.kwargs["reference_tag"],
            tx.pk,
        )
        return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)


class InternalTransferView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BaseWalletTransferSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logger.info(
            "internal_transfer_attempt user_id=%s from_reference_tag=%s to_reference_tag=%s",
            request.user.pk,
            serializer.validated_data["from_reference_tag"],
            serializer.validated_data["to_reference_tag"],
        )
        tx = MoneyFlowService.internal_transfer(
            user=request.user,
            from_reference_tag=serializer.validated_data["from_reference_tag"],
            to_reference_tag=serializer.validated_data["to_reference_tag"],
            amount=serializer.validated_data["amount"],
            metadata=serializer.validated_data.get("metadata", {}),
        )
        logger.info(
            "internal_transfer_success user_id=%s tx_id=%s",
            request.user.pk,
            tx.pk,
        )
        return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)


class P2PSendHoldView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BaseWalletTransferSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logger.info(
            "p2p_send_attempt user_id=%s from_reference_tag=%s to_reference_tag=%s",
            request.user.pk,
            serializer.validated_data["from_reference_tag"],
            serializer.validated_data["to_reference_tag"],
        )
        tx = MoneyFlowService.p2p_send_hold(
            user=request.user,
            from_reference_tag=serializer.validated_data["from_reference_tag"],
            to_reference_tag=serializer.validated_data["to_reference_tag"],
            amount=serializer.validated_data["amount"],
            metadata=serializer.validated_data.get("metadata", {}),
        )
        logger.info(
            "p2p_send_success user_id=%s tx_id=%s",
            request.user.pk,
            tx.pk,
        )
        return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)


class WalletTransactionHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionHistorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Transaction.objects.none()
        reference_tag = self.kwargs.get("reference_tag")
        if not reference_tag:
            return Transaction.objects.none()

        wallet = Wallet.objects.filter(
            reference_tag=reference_tag, user=self.request.user
        ).first()
        if not wallet:
            raise ValidationError({"wallet": _("Wallet not found.")})

        qs = (
            Transaction.objects.filter(Q(from_wallet=wallet) | Q(to_wallet=wallet))
            .select_related("from_wallet", "to_wallet")
            .order_by("-created_at", "-id")
        )
        logger.info(
            "wallet_tx_history user_id=%s reference_tag=%s",
            self.request.user.pk,
            reference_tag,
        )
        return qs


class UserTransactionHistoryView(generics.ListAPIView):
    """
    GET /api/v1/transactions/
    Optional: wallet_tag filter
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TransactionHistorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Transaction.objects.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return Transaction.objects.none()

        qs = (
            Transaction.objects.filter(
                Q(from_wallet__user=user) | Q(to_wallet__user=user)
            )
            .select_related("from_wallet", "to_wallet")
            .order_by("-created_at", "-id")
        )

        logger.info("user_tx_history user_id=%s", user.pk)

        return qs


class TransactionActionView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionActionSerializer

    def create(self, request, *args, **kwargs):
        serializer = TransactionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tx_id = self.kwargs["tx_id"]

        logger.info(
            "p2p_action user_id=%s tx_id=%s is_accepted=%s",
            request.user.pk,
            tx_id,
            serializer.validated_data["is_accepted"],
        )

        if serializer.validated_data["is_accepted"]:
            tx = MoneyFlowService.p2p_accept(user=request.user, tx_id=tx_id)
        else:
            tx = MoneyFlowService.p2p_reject(user=request.user, tx_id=tx_id)

        return Response(TransactionSerializer(tx).data, status=status.HTTP_200_OK)
