import logging

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _

from users.models import UserAccessToken

logger = logging.getLogger(__name__)


class VersionedJWTAuthentication(JWTAuthentication):
    """
    Reject JWT if the token_version claim does not match user's current token_version.
    This allows immediate invalidation (e.g., after a passcode change).
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        token_tv = validated_token.get("tv")
        if token_tv is None:
            logger.warning(
                "token_missing_version user_id=%s", getattr(user, "pk", None)
            )
            raise AuthenticationFailed(_("Invalid token (missing version)."))

        if int(token_tv) != int(getattr(user, "token_version", 1)):
            logger.warning(
                "token_version_mismatch user_id=%s token_tv=%s user_tv=%s",
                getattr(user, "pk", None),
                token_tv,
                getattr(user, "token_version", None),
            )
            raise AuthenticationFailed(
                _("Token is no longer valid. Please log in again.")
            )

        token_jti = validated_token.get("jti")
        if not token_jti:
            logger.warning("token_missing_jti user_id=%s", getattr(user, "pk", None))
            raise AuthenticationFailed(_("Invalid token (missing identifier)."))

        now = timezone.now()
        idle_seconds = getattr(settings, "ACCESS_TOKEN_IDLE_TIMEOUT_SECONDS", 120)
        expires_at = now + timedelta(seconds=idle_seconds)

        token_record = UserAccessToken.objects.filter(jti=token_jti, user=user).first()
        if not token_record or token_record.expires_at <= now:
            logger.info(
                "token_session_expired user_id=%s jti=%s",
                getattr(user, "pk", None),
                token_jti,
            )
            raise AuthenticationFailed(_("Session expired. Please log in again."))

        token_record.last_seen_at = now
        token_record.expires_at = expires_at
        token_record.save(update_fields=["last_seen_at", "expires_at"])

        return user
