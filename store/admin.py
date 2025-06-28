from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'documentId', 'slug', 'display_image', 'createdAt', 'publishedAt')
    search_fields = ('name', 'documentId')
    list_filter = ('publishedAt',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('display_image',)
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    display_image.short_description = 'Image'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'mrp', 'sellingPice', 'ItemQuantityType', 'display_image', 'is_featured', 'is_active')
    list_filter = ('is_featured', 'is_active', 'categories')
    search_fields = ('name', 'description')
    filter_horizontal = ('categories',)
    readonly_fields = ('display_image',)
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    display_image.short_description = 'Image'
    