from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionType(models.TextChoices):
    DEPOSIT = "deposit", _("Deposit")
    INTERNAL = "internal", _("Internal transfer")
    P2P = "p2p", _("Peer to peer")


class TransactionStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    COMPLETED = "completed", _("Completed")
    REJECTED = "rejected", _("Rejected")
    CANCELED = "canceled", _("Canceled")


class TransactionDirectionChoices(models.TextChoices):
    INCOMING = "incoming", _("Incoming")
    OUTGOING = "outgoing", _("Outgoing")
    DEPOSIT = "deposit", _("Deposit")
    INTERNAL = "internal", _("Internal")
