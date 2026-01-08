from django.db import models
from django.utils.translation import gettext_lazy as _


class WalletType(models.TextChoices):
    CURRENT = "current", _("Current")
    SAVINGS = "savings", _("Savings")
    TRAVEL = "travel", _("Travel")
    BUSINESS = "business", _("Business")
    OTHER = "other", _("Other")


class WalletStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    SUSPENDED = "suspended", _("Suspended")
    CLOSED = "closed", _("Closed")
