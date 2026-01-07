import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import RegisterSerializer, ChangePasscodeSerializer

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        logger.info("user_register_success user_id=%s", user.pk)


class ChangePasscodeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasscodeSerializer

    def post(self, request, *args, **kwargs):
        logger.info("passcode_change_attempt user_id=%s", request.user.pk)
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info(
            "passcode_change_success user_id=%s token_version=%s",
            user.pk,
            user.token_version,
        )
        return Response(
            {"detail": "Passcode changed successfully."}, status=status.HTTP_200_OK
        )
