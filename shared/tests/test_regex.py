from django.test import SimpleTestCase
from rest_framework import serializers

from shared.regex import PasscodeField


class PasscodeFieldTests(SimpleTestCase):
    def test_accepts_six_digits(self):
        field = PasscodeField()
        self.assertEqual(field.run_validation("123456"), "123456")

    def test_rejects_invalid_value(self):
        field = PasscodeField()
        with self.assertRaises(serializers.ValidationError):
            field.run_validation("12345")
