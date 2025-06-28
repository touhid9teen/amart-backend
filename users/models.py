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
    def create_user(self, phone_number, country_code='+1', password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        user = self.model(phone_number=phone_number, country_code=country_code, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, country_code='+1', password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, country_code, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Remove username field
    country_code = models.CharField(max_length=5, default='+880')  # Default to US
    phone_number = models.CharField(max_length=15, unique=True)  # Make phone_number unique
    is_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['country_code']
    
    objects = UserManager()
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['country_code', 'phone_number'], 
                name='unique_phone_with_country'
            )
        ]
    
    @property
    def full_phone(self):
        """Return the full phone number with country code"""
        return f"{self.country_code}{self.phone_number}"
    
    def __str__(self):
        return self.full_phone

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.full_phone} - {self.otp}"
