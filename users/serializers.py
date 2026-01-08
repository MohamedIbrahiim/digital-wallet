import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from shared.regex import PasscodeField
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    mobile_number = PhoneNumberField()
    passcode = PasscodeField()
    passcode_confirm = PasscodeField()

    class Meta:
        model = User
        fields = (
            "mobile_number",
            "first_name",
            "last_name",
            "passcode",
            "passcode_confirm",
        )

    def validate(self, attrs):
        passcode = attrs.get("passcode")
        confirm = attrs.get("passcode_confirm")

        if passcode != confirm:
            raise serializers.ValidationError(
                {"passcode_confirm": _("Passcodes do not match.")}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("passcode_confirm")
        passcode = validated_data.pop("passcode")

        user = User(**validated_data)
        user.set_password(passcode)
        user.save()
        logger.info("user_register_persisted user_id=%s", user.pk)
        return user


class ChangePasscodeSerializer(serializers.Serializer):
    old_passcode = PasscodeField()
    new_passcode = PasscodeField()
    new_passcode_confirm = PasscodeField()

    def validate(self, attrs):
        new_passcode = attrs.get("new_passcode")
        confirm = attrs.get("new_passcode_confirm")

        if new_passcode != confirm:
            raise serializers.ValidationError(
                {"new_passcode_confirm": _("Passcodes do not match.")}
            )

        return attrs

    def validate_old_passcode(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Old passcode is incorrect."))
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        new_passcode = self.validated_data["new_passcode"]

        with transaction.atomic():
            user.set_password(new_passcode)
            user.token_version = user.token_version + 1
            user.save(update_fields=["password", "token_version"])

        logger.info(
            "passcode_changed user_id=%s token_version=%s", user.pk, user.token_version
        )
        return user
