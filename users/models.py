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


class UserAccessToken(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="access_tokens"
    )
    jti = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField()
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = _("Access token")
        verbose_name_plural = _("Access tokens")
        indexes = [
            models.Index(fields=["user", "expires_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.jti}"

    @classmethod
    def touch(cls, *, user, jti: str, expires_at) -> "UserAccessToken":
        now = timezone.now()
        token, _ = cls.objects.update_or_create(
            jti=jti,
            defaults={
                "user": user,
                "last_seen_at": now,
                "expires_at": expires_at,
            },
        )
        return token
