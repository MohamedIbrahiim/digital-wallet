import logging

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _

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

        return user
