import logging

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from wallets.models import Wallet
from .permissions import IsWalletOwner
from .serializers import WalletSerializer

logger = logging.getLogger(__name__)


class WalletViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, IsWalletOwner]
    serializer_class = WalletSerializer
    lookup_field = "reference_tag"
    lookup_url_kwarg = "reference_tag"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Wallet.objects.none()
        queryset = Wallet.objects.filter(user=self.request.user).order_by("-created_at")
        logger.info("wallet_list_requested user_id=%s", self.request.user.pk)
        return queryset

    def perform_create(self, serializer):
        wallet = serializer.save()
        logger.info(
            "wallet_create_success user_id=%s wallet_id=%s name=%s",
            wallet.user_id,
            wallet.pk,
            wallet.name,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="reference_tag",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Wallet reference tag (e.g., @wlt_x7k9f.1).",
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        logger.info(
            "wallet_retrieve_requested user_id=%s reference_tag=%s",
            request.user.pk,
            kwargs.get("reference_tag"),
        )
        return super().retrieve(request, *args, **kwargs)
