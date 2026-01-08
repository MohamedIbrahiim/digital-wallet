import logging

from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class IsWalletOwner(BasePermission):
    message = _("You do not have permission to access this wallet.")

    def has_object_permission(self, request, view, obj):
        is_owner = obj.user_id == request.user.id
        if not is_owner:
            logger.warning(
                "wallet_permission_denied user_id=%s wallet_id=%s",
                request.user.id,
                obj.pk,
            )
        return is_owner
