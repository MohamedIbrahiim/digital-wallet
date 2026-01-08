import logging
import time
from datetime import timedelta
from typing import Optional, Tuple

from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from shared.auth.authentication import VersionedJWTAuthentication
from users.models import UserAccessToken

logger = logging.getLogger(__name__)


class SlidingAccessTokenMiddleware:
    """
    Rolling access token with minimal churn:
    - Access lifetime: 2 minutes (configured in SIMPLE_JWT)
    - If remaining lifetime < ROLLING_THRESHOLD_SECONDS -> issue a new token
    - Return new token in response header: X-Access-Token
    """

    ROLLING_THRESHOLD_SECONDS = 30  # mint new token only if < 30s remaining

    def __init__(self, get_response):
        self.get_response = get_response
        self.auth = VersionedJWTAuthentication()

    def _authenticate(self, request) -> Optional[Tuple[object, object]]:
        try:
            return self.auth.authenticate(request)  # (user, validated_token) or None
        except (InvalidToken, TokenError):
            logger.debug("rolling_token_invalid")
            return None

    def __call__(self, request):
        auth_result = self._authenticate(request)

        response = self.get_response(request)

        # Only roll on authenticated requests and successful-ish responses
        if not auth_result:
            return response

        _, validated_token = auth_result
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return response

        exp = validated_token.get("exp")
        if not exp:
            logger.debug("rolling_token_missing_exp user_id=%s", request.user.pk)
            return response

        now = int(time.time())
        remaining = int(exp) - now

        # Mint new token only if close to expiry
        if remaining <= self.ROLLING_THRESHOLD_SECONDS:
            new_token = AccessToken.for_user(request.user)
            new_token["tv"] = request.user.token_version
            response["X-Access-Token"] = str(new_token)
            response["Access-Control-Expose-Headers"] = "X-Access-Token"
            idle_seconds = getattr(settings, "ACCESS_TOKEN_IDLE_TIMEOUT_SECONDS", 120)
            expires_at = timezone.now() + timedelta(seconds=idle_seconds)
            UserAccessToken.touch(
                user=request.user,
                jti=str(new_token["jti"]),
                expires_at=expires_at,
            )
            logger.info(
                "rolling_token_issued user_id=%s remaining_seconds=%s",
                request.user.pk,
                remaining,
            )

        return response
