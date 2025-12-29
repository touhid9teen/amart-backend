from django.contrib import admin
from .models import User, OTP, Country

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'flag_emoji', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_verified', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_verified', 'is_active')

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at', 'is_used')
    search_fields = ('user__email', 'otp')
    list_filter = ('is_used', 'created_at')
