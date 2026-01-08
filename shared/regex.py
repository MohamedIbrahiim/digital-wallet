import re

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class PasscodeField(serializers.RegexField):
    def __init__(self, enforce_strength: bool = True, **kwargs):
        self._enforce_strength = enforce_strength
        super().__init__(
            regex=r"^\d{6}$",
            write_only=True,
            error_messages={"invalid": _("Passcode must be exactly 6 digits.")},
            **kwargs,
        )

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if self._enforce_strength:
            if self._is_sequential(value):
                raise serializers.ValidationError(_("Passcode cannot be sequential."))
            if self._is_repetitive(value):
                raise serializers.ValidationError(
                    _("Passcode cannot contain repetitive patterns.")
                )
        return value

    @staticmethod
    def _is_sequential(value: str) -> bool:
        digits = [int(char) for char in value]
        if all(digits[i] + 1 == digits[i + 1] for i in range(len(digits) - 1)):
            return True
        if all(digits[i] - 1 == digits[i + 1] for i in range(len(digits) - 1)):
            return True
        return False

    @staticmethod
    def _is_repetitive(value: str) -> bool:
        # consecutive duplicate digits (e.g. 001234, 112233)
        if re.search(r"(.)\1", value):
            return True
        # repeated patterns (e.g. 121212, 123123)
        if value == value[:2] * 3:
            return True
        if value == value[:3] * 2:
            return True
        return False
