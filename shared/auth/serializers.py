import logging

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

logger = logging.getLogger(__name__)


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["tv"] = user.token_version
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data.pop("refresh", None)  # no refresh
        logger.info("login_success user_id=%s", getattr(self.user, "pk", None))
        return data
