from rest_framework import serializers
from .models import Category, Product, UserCart
import base64
import uuid
from django.core.files.base import ContentFile


class UserCartSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = UserCart
        fields = ['id', 'user', 'product', 'product_name', 'quantity', 'amount', 'added_at']
        read_only_fields = ['amount', 'added_at', 'user']

    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data['product']
        quantity = validated_data['quantity']

        cart_item, created = UserCart.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': quantity, 'amount': quantity * product.sellingPice}
        )
        if not created:
            cart_item.quantity += quantity  
            cart_item.amount = cart_item.quantity * product.sellingPice
            cart_item.save()
        return cart_item


class Base64ImageField(serializers.ImageField):
    """
    A custom field to handle base64-encoded image uploads
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            # Base64 encoded image - decode
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'{uuid.uuid4()}.{ext}')
        return super().to_internal_value(data)

class CategorySerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Category
        fields = ['id', 'documentId', 'name', 'colore', 'slug', 'image', 
                 'image_alt', 'createdAt', 'updatedAt', 'publishedAt']
        read_only_fields = ['id', 'createdAt', 'updatedAt', 'publishedAt', 'slug']

class ProductListSerializer(serializers.ModelSerializer):
    categories = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'mrp', 'sellingPice', 'ItemQuantityType', 'image', 'categories', 'is_featured']

class ProductDetailSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,                            
        required=False
    )
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'mrp', 'sellingPice', 'ItemQuantityType', 
                 'image', 'image_alt', 'categories', 'category_ids',
                 'createdAt', 'updatedAt', 'is_featured', 'is_active']
        read_only_fields = ['id', 'createdAt', 'updatedAt']
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        
        product = Product.objects.create(**validated_data)
        
        # Add categories
        for category_id in category_ids:
            try:
                category = Category.objects.get(id=category_id)
                product.categories.add(category)
            except Category.DoesNotExist:
                pass
        
        return product
    
    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        
        # Update product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update categories if provided
        if category_ids is not None:
            instance.categories.clear()  # Remove existing categories
            for category_id in category_ids:
                try:
                    category = Category.objects.get(id=category_id)
                    instance.categories.add(category)
                except Category.DoesNotExist:
                    pass
        
        return instance
