from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class PasscodeField(serializers.RegexField):
    def __init__(self, **kwargs):
        super().__init__(
            regex=r"^\d{6}$",
            write_only=True,
            error_messages={"invalid": _("Passcode must be exactly 6 digits.")},
            **kwargs,
        )
