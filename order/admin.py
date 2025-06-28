from django.contrib import admin
from .models import Order, OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'address', 'total_amount', 'delivery_charge', 'status', 'created_at')
    search_fields = ('user__username', 'address', 'status')
    list_filter = ('status', 'created_at')
    date_hierarchy = 'created_at'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity')
    search_fields = ('product__name',)
    list_filter = ('order',)
