import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.models import UserAccessToken

logger = logging.getLogger(__name__)


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["tv"] = user.token_version
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        access_token = AccessToken(data["access"])
        idle_seconds = getattr(settings, "ACCESS_TOKEN_IDLE_TIMEOUT_SECONDS", 120)
        expires_at = timezone.now() + timedelta(seconds=idle_seconds)
        UserAccessToken.touch(
            user=self.user,
            jti=str(access_token["jti"]),
            expires_at=expires_at,
        )
        data.pop("refresh", None)  # no refresh
        logger.info("login_success user_id=%s", getattr(self.user, "pk", None))
        return data
