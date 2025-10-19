import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("date_joined", timezone.now())

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("date_joined", timezone.now())

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None  # disable username
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("VO", "View Only"),
        ("PM", "Project Manager"),
        ("OM", "Operations Manager"),
        ("EG", "Engineer"),
    ]
    has_seen_welcome = models.BooleanField(default=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, default="VO")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    token_version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_archived:
            self.role = "VO"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.get_role_display()}"

    @property
    def full_name(self):
        """Return the user's full name, fallback to email if no name"""
        first_name = self.user.first_name.strip()
        last_name = self.user.last_name.strip()
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return self.user.email