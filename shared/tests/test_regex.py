from django.test import SimpleTestCase
from rest_framework import serializers

from shared.regex import PasscodeField


class PasscodeFieldTests(SimpleTestCase):
    def test_accepts_six_digits(self):
        field = PasscodeField()
        self.assertEqual(field.run_validation("907284"), "907284")

    def test_rejects_invalid_value(self):
        field = PasscodeField()
        with self.assertRaises(serializers.ValidationError):
            field.run_validation("12345")

    def test_rejects_incremental_sequence(self):
        field = PasscodeField()
        with self.assertRaises(serializers.ValidationError):
            field.run_validation("123456")

    def test_rejects_decremental_sequence(self):
        field = PasscodeField()
        with self.assertRaises(serializers.ValidationError):
            field.run_validation("654321")

    def test_rejects_consecutive_duplicates(self):
        field = PasscodeField()
        with self.assertRaises(serializers.ValidationError):
            field.run_validation("001234")

    def test_rejects_repeated_pattern(self):
        field = PasscodeField()
        with self.assertRaises(serializers.ValidationError):
            field.run_validation("121212")

    def test_rejects_repeated_triplet_pattern(self):
        field = PasscodeField()
        with self.assertRaises(serializers.ValidationError):
            field.run_validation("123123")
