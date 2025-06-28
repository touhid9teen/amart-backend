from rest_framework import serializers
from .models import Order, OrderItem
from store.models import Product

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)
    product = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product', 'quantity']

    def get_product(self, obj):
        return {
            'id': obj.product.id,
            'name': obj.product.name,
            'image': obj.product.image.url if obj.product.image else '',
            'price': obj.product.sellingPice
        }

    def create(self, validated_data):
        product_id = validated_data.pop('product_id')
        product = Product.objects.get(id=product_id)
        return OrderItem(product=product, **validated_data)

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'order_id', 'user', 'created_at', 'address', 'total_amount', 'delivery_charge', 'status', 'order_notes', 'items']
        read_only_fields = ['user', 'created_at', 'status', 'order_id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            raise serializers.ValidationError('User must be provided to create an order.')
        user = request.user
        order = Order.objects.create(**validated_data, user=user)
        for item_data in items_data:
            item = OrderItemSerializer().create(item_data)
            item.order = order
            item.save()
        return order