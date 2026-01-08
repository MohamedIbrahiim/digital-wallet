from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, mobile_number, password=None, **extra_fields):
        user = self.model(mobile_number=mobile_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        user = self.create_user(
            mobile_number=mobile_number, password=password, **extra_fields
        )
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Mobile-based user for Digital Wallet.
    - mobile_number is the login identifier
    - passcode is stored using Django's password hashing (set_password/check_password)
    """

    mobile_number = PhoneNumberField(
        unique=True, db_index=True, verbose_name=_("Mobile number")
    )
    first_name = models.CharField(max_length=50, blank=True, default="")
    last_name = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    preferred_language = models.CharField(
        max_length=5,
        choices=[("en", _("English")), ("ar", _("Arabic"))],
        default="en",
    )
    token_version = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Optional but useful for auditing / sorting
    date_joined = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return str(self.mobile_number)
