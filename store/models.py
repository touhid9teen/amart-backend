from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
import os

# Image path functions removed - now using URLField for external image URLs

class Category(models.Model):
    documentId = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    colore = models.CharField(max_length=50, null=True, blank=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    # Add image field directly to Category model
    image = models.URLField(max_length=500, null=True, blank=True)
    image_alt = models.CharField(max_length=255, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    publishedAt = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        # Image deletion removed - now using external URLs
        super().delete(*args, **kwargs)

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    short_description = models.CharField(max_length=500, blank=True, default="")
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    sellingPice = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ItemQuantityType = models.CharField(max_length=50)  # e.g., kg, g, piece, etc.
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    # Add image field directly to Product model
    image = models.URLField(max_length=500, null=True, blank=True)
    image_alt = models.CharField(max_length=255, blank=True)
    categories = models.ManyToManyField(Category, related_name='products', blank=True)
    brand = models.ForeignKey(
        'admin_dashboard.Brand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    tags = models.JSONField(default=list, blank=True)  # Array of tag strings
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    class Meta:
        ordering = ['-createdAt']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            self.slug = slugify(self.name) + '-' + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        # Image deletion removed - now using external URLs
        super().delete(*args, **kwargs)


# Cart Items table


class UserCart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # calculated as quantity * product.sellingPice
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.product.sellingPice
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.phone_number} - {self.product.name} ({self.quantity})"
