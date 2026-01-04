from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid

class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=5)  # e.g., +1, +44, +91
    flag_emoji = models.CharField(max_length=10, blank=True, null=True)  # Optional emoji flag
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Remove username field
    email = models.EmailField(unique=True)  # Email is primary for authentication
    # country_code = models.CharField(max_length=5, blank=True, null=True)  # Commented: Optional, for future phone auth
    # phone_number = models.CharField(max_length=15, blank=True, null=True)  # Commented: Optional, for future phone auth
    is_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    def __str__(self):
        return self.email

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.email} - {self.otp}"
