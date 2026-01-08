from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _message_for_integrity_error(exc: IntegrityError) -> str:
    message = str(exc)
    lower_message = message.lower()

    if "users_user_mobile_number_key" in message or "mobile_number" in lower_message:
        return _("An account with this mobile number already exists.")

    if "uniq_wallet_name_per_user_ci" in message or (
        "wallets_wallet" in lower_message and "name" in lower_message
    ):
        return _("You already have a wallet with this name.")

    if (
        "wallets_wallet_reference_tag_key" in message
        or "reference_tag" in lower_message
    ):
        return _("A wallet reference tag conflict occurred. Please retry.")

    if (
        "wallet_balance_non_negative" in message
        or "wallet_held_balance_non_negative" in message
    ):
        return _("Wallet balance cannot be negative.")

    if "hold_must_be_pending" in message:
        return _("This action is only allowed for pending transactions.")

    return _("Request violates a data constraint. Please review your input.")


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, IntegrityError):
        detail = _message_for_integrity_error(exc)
        return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

    return response
