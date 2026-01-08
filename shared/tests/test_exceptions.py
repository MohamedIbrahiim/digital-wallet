from django.db import IntegrityError
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from shared.exceptions import _message_for_integrity_error, api_exception_handler


class ExceptionHandlerTests(SimpleTestCase):
    def test_message_for_mobile_number_conflict(self):
        error = IntegrityError("users_user_mobile_number_key")
        self.assertIn("mobile number", str(_message_for_integrity_error(error)))

    def test_message_for_wallet_name_conflict(self):
        error = IntegrityError("uniq_wallet_name_per_user_ci")
        self.assertIn("wallet with this name", str(_message_for_integrity_error(error)))

    def test_message_for_reference_tag_conflict(self):
        error = IntegrityError("wallets_wallet_reference_tag_key")
        self.assertIn("reference tag", str(_message_for_integrity_error(error)))

    def test_message_for_balance_constraint(self):
        error = IntegrityError("wallet_balance_non_negative")
        self.assertIn(
            "balance cannot be negative", str(_message_for_integrity_error(error))
        )

    def test_message_for_pending_hold(self):
        error = IntegrityError("hold_must_be_pending")
        self.assertIn("pending", str(_message_for_integrity_error(error)))

    def test_message_for_unknown_constraint(self):
        error = IntegrityError("some_other_constraint")
        self.assertIn("data constraint", str(_message_for_integrity_error(error)))

    def test_api_exception_handler_integrity_error(self):
        error = IntegrityError("users_user_mobile_number_key")
        response = api_exception_handler(error, context={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("mobile number", str(response.data["detail"]))

    def test_api_exception_handler_passthrough(self):
        error = ValidationError({"field": "invalid"})
        response = api_exception_handler(error, context={"request": None, "view": None})
        self.assertEqual(response.status_code, 400)

    def test_api_exception_handler_unknown_returns_none(self):
        response = api_exception_handler(ValueError("boom"), context={})
        self.assertIsNone(response)
