from rest_framework import serializers


class PasscodeField(serializers.RegexField):
    def __init__(self, **kwargs):
        super().__init__(
            regex=r"^\d{6}$",
            write_only=True,
            error_messages={"invalid": "Passcode must be exactly 6 digits."},
            **kwargs,
        )
