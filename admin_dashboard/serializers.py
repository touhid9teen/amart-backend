from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from store.models import Category, Product
from order.models import Order, OrderItem
from admin_dashboard.models import Brand, Review, Coupon, InventoryLog, SystemSetting

User = get_user_model()


# ──────────────────────────────────────────────
#  AUTH SERIALIZERS
# ──────────────────────────────────────────────

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=6, write_only=True)

    def validate_email(self, value):
        return value.lower().strip()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email, role__in=['admin', 'superadmin'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No admin account found with this email."})

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid password."})

        if not user.is_active:
            raise serializers.ValidationError({"non_field": "This admin account has been deactivated."})

        data['user'] = user
        return data


class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined', 'last_login']


# ──────────────────────────────────────────────
#  BRAND SERIALIZERS
# ──────────────────────────────────────────────

class BrandSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'slug', 'description', 'website',
            'products_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'products_count', 'created_at', 'updated_at']

    def get_products_count(self, obj):
        return obj.products.count()


# ──────────────────────────────────────────────
#  CATEGORY SERIALIZERS (ADMIN)
# ──────────────────────────────────────────────

class AdminCategoryListSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)

    class Meta:
        model = Category
        fields = [
            'id', 'documentId', 'name', 'slug', 'description',
            'parent', 'parent_name', 'image', 'image_alt',
            'products_count', 'createdAt', 'updatedAt'
        ]
        read_only_fields = ['id', 'slug', 'products_count', 'createdAt', 'updatedAt', 'createdAt', 'updatedAt']


class AdminCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id', 'documentId', 'name', 'slug', 'description',
            'parent', 'image', 'image_alt', 'colore',
            'createdAt', 'updatedAt', 'publishedAt'
        ]
        read_only_fields = ['id', 'slug', 'createdAt', 'updatedAt', 'publishedAt']

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        if len(value) > 100:
            raise serializers.ValidationError("Name must not exceed 100 characters.")
        return value

    def create(self, validated_data):
        if not validated_data.get('slug'):
            validated_data['slug'] = slugify(validated_data['name'])
        if not validated_data.get('documentId'):
            import uuid
            validated_data['documentId'] = str(uuid.uuid4())[:8]
        return super().create(validated_data)


# ──────────────────────────────────────────────
#  PRODUCT SERIALIZERS (ADMIN)
# ──────────────────────────────────────────────

class AdminProductListSerializer(serializers.ModelSerializer):
    category_names = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source='brand.name', read_only=True, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'mrp', 'sellingPice', 'discount_price',
            'stock', 'sku', 'ItemQuantityType', 'image',
            'category_names', 'brand_name', 'brand',
            'is_featured', 'status', 'is_active',
            'createdAt', 'updatedAt'
        ]
        read_only_fields = ['id', 'slug', 'createdAt', 'updatedAt']

    def get_category_names(self, obj):
        return [cat.name for cat in obj.categories.all()]


class AdminProductSerializer(serializers.ModelSerializer):
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    categories = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'mrp', 'sellingPice', 'discount_price',
            'stock', 'sku', 'ItemQuantityType',
            'image', 'image_alt', 'tags',
            'category_ids', 'categories',
            'brand',
            'is_featured', 'status', 'is_active',
            'createdAt', 'updatedAt'
        ]
        read_only_fields = ['id', 'slug', 'createdAt', 'updatedAt']

    def get_categories(self, obj):
        return [{'id': cat.id, 'name': cat.name} for cat in obj.categories.all()]

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        if len(value) > 200:
            raise serializers.ValidationError("Name must not exceed 200 characters.")
        return value

    def validate_sellingPice(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value

    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        product = Product.objects.create(**validated_data)
        for cat_id in category_ids:
            try:
                cat = Category.objects.get(id=cat_id)
                product.categories.add(cat)
            except Category.DoesNotExist:
                pass
        return product

    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if category_ids is not None:
            instance.categories.clear()
            for cat_id in category_ids:
                try:
                    cat = Category.objects.get(id=cat_id)
                    instance.categories.add(cat)
                except Category.DoesNotExist:
                    pass
        return instance


# ──────────────────────────────────────────────
#  ORDER SERIALIZERS (ADMIN)
# ──────────────────────────────────────────────

class AdminOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.CharField(source='product.image', read_only=True, allow_null=True)
    product_price = serializers.DecimalField(
        source='product.sellingPice', read_only=True, max_digits=10, decimal_places=2
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'product_price', 'quantity']


class AdminOrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source='user.email', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'customer_name', 'customer_email',
            'total_amount', 'delivery_charge', 'status',
            'items_count', 'created_at'
        ]

    def get_customer_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

    def get_items_count(self, obj):
        return obj.items.count()


class AdminOrderSerializer(serializers.ModelSerializer):
    items = AdminOrderItemSerializer(many=True, read_only=True)
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'customer', 'address',
            'total_amount', 'delivery_charge', 'status',
            'order_notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_id', 'customer', 'address',
            'total_amount', 'delivery_charge',
            'order_notes', 'items', 'created_at', 'updated_at'
        ]

    def get_customer(self, obj):
        return {
            'id': str(obj.user.id),
            'email': obj.user.email,
            'name': f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email,
        }


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        'pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded'
    ])


# ──────────────────────────────────────────────
#  CUSTOMER SERIALIZERS
# ──────────────────────────────────────────────

class AdminCustomerListSerializer(serializers.ModelSerializer):
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'is_active', 'is_verified',
            'total_orders', 'total_spent',
            'date_joined', 'last_login'
        ]

    def get_total_orders(self, obj):
        return obj.orders.count()

    def get_total_spent(self, obj):
        from django.db.models import Sum
        result = obj.orders.filter(status__in=['delivered', 'shipped', 'processing']).aggregate(
            total=Sum('total_amount')
        )
        return result['total'] or 0


class AdminCustomerSerializer(serializers.ModelSerializer):
    recent_orders = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'is_active', 'is_verified', 'role',
            'date_joined', 'last_login',
            'recent_orders'
        ]
        read_only_fields = [
            'id', 'email', 'first_name', 'last_name',
            'is_verified', 'role',
            'date_joined', 'last_login',
            'recent_orders'
        ]

    def get_recent_orders(self, obj):
        orders = obj.orders.order_by('-created_at')[:5]
        return [
            {
                'id': str(order.order_id),
                'total_amount': order.total_amount,
                'status': order.status,
                'created_at': order.created_at
            }
            for order in orders
        ]


# ──────────────────────────────────────────────
#  REVIEW SERIALIZERS
# ──────────────────────────────────────────────

class AdminReviewListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name',
            'customer_email', 'customer_name',
            'rating', 'comment', 'status',
            'created_at'
        ]

    def get_customer_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


# ──────────────────────────────────────────────
#  COUPON SERIALIZERS
# ──────────────────────────────────────────────

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value',
            'min_order_amount', 'max_uses', 'current_uses',
            'is_active', 'start_date', 'expiry_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_uses', 'created_at', 'updated_at']

    def validate_code(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Code must be at least 3 characters.")
        if len(value) > 20:
            raise serializers.ValidationError("Code must not exceed 20 characters.")
        return value.upper().strip()

    def validate_discount_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Discount value must be positive.")
        return value


# ──────────────────────────────────────────────
#  INVENTORY SERIALIZERS
# ──────────────────────────────────────────────

class AdminInventoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'image',
            'stock', 'createdAt'
        ]


class AdminInventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'image',
            'stock', 'createdAt', 'updatedAt'
        ]


class InventoryAdjustSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True)
    reason = serializers.CharField(required=True, max_length=255)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product not found.")
        return value

    def validate_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("Quantity must be non-zero.")
        return value


# ──────────────────────────────────────────────
#  ANALYTICS SERIALIZER (for structured outputs)
# ──────────────────────────────────────────────

class SalesTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_items = serializers.IntegerField()


class TopProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class RevenueDataSerializer(serializers.Serializer):
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    orders = serializers.IntegerField()


# ──────────────────────────────────────────────
#  SETTINGS SERIALIZERS
# ──────────────────────────────────────────────

class StoreSettingsSerializer(serializers.Serializer):
    store_name = serializers.CharField(max_length=200, default="My Store")
    store_email = serializers.EmailField(allow_blank=True, default="")
    store_phone = serializers.CharField(max_length=20, allow_blank=True, default="")
    address = serializers.CharField(max_length=500, allow_blank=True, default="")
    currency = serializers.CharField(max_length=10, default="BDT")
    currency_symbol = serializers.CharField(max_length=10, default="৳")
    timezone = serializers.CharField(max_length=50, default="Asia/Dhaka")
    logo_url = serializers.URLField(allow_blank=True, default="")
    favicon_url = serializers.URLField(allow_blank=True, default="")


class TaxSettingsSerializer(serializers.Serializer):
    tax_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_included_in_price = serializers.BooleanField(default=False)
    tax_name = serializers.CharField(max_length=100, default="VAT")
    tax_id = serializers.CharField(max_length=100, allow_blank=True, default="")
    enable_tax = serializers.BooleanField(default=False)


class ShippingSettingsSerializer(serializers.Serializer):
    free_shipping_min_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    standard_shipping_charge = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    express_shipping_charge = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_delivery_days = serializers.IntegerField(default=3)
    shipping_zones = serializers.ListField(child=serializers.CharField(), default=list)
    enable_free_shipping = serializers.BooleanField(default=False)


class PaymentSettingsSerializer(serializers.Serializer):
    accepted_cards = serializers.ListField(child=serializers.CharField(), default=list)
    cod_enabled = serializers.BooleanField(default=True)
    online_payment_enabled = serializers.BooleanField(default=False)
    bkash_enabled = serializers.BooleanField(default=False)
    nagad_enabled = serializers.BooleanField(default=False)
    rocket_enabled = serializers.BooleanField(default=False)
    bkash_number = serializers.CharField(max_length=20, allow_blank=True, default="")
    nagad_number = serializers.CharField(max_length=20, allow_blank=True, default="")
    rocket_number = serializers.CharField(max_length=20, allow_blank=True, default="")


class EmailSettingsSerializer(serializers.Serializer):
    smtp_host = serializers.CharField(max_length=200, default="smtp.gmail.com")
    smtp_port = serializers.IntegerField(default=587)
    smtp_username = serializers.CharField(max_length=200, allow_blank=True, default="")
    smtp_password = serializers.CharField(max_length=200, allow_blank=True, default="", write_only=True)
    smtp_use_tls = serializers.BooleanField(default=True)
    from_email = serializers.EmailField(allow_blank=True, default="")
    order_notification_emails = serializers.ListField(
        child=serializers.EmailField(), default=list
    )


class NotificationSettingsSerializer(serializers.Serializer):
    email_notifications = serializers.BooleanField(default=True)
    order_confirmation = serializers.BooleanField(default=True)
    order_shipped = serializers.BooleanField(default=True)
    order_delivered = serializers.BooleanField(default=True)
    new_order_admin = serializers.BooleanField(default=True)
    low_stock_alert = serializers.BooleanField(default=True)
    low_stock_threshold = serializers.IntegerField(default=10)
    new_customer_signup = serializers.BooleanField(default=True)


# ──────────────────────────────────────────────
#  SETTING GROUP MAPPING
# ──────────────────────────────────────────────

SETTING_SERIALIZER_MAP = {
    'store': StoreSettingsSerializer,
    'tax': TaxSettingsSerializer,
    'shipping': ShippingSettingsSerializer,
    'payment': PaymentSettingsSerializer,
    'email': EmailSettingsSerializer,
    'notification': NotificationSettingsSerializer,
}

SETTING_DEFAULTS = {
    'store': {
        'store_name': 'My Store',
        'store_email': '',
        'store_phone': '',
        'address': '',
        'currency': 'BDT',
        'currency_symbol': '৳',
        'timezone': 'Asia/Dhaka',
        'logo_url': '',
        'favicon_url': '',
    },
    'tax': {
        'tax_percentage': 0,
        'tax_included_in_price': False,
        'tax_name': 'VAT',
        'tax_id': '',
        'enable_tax': False,
    },
    'shipping': {
        'free_shipping_min_amount': 0,
        'standard_shipping_charge': 0,
        'express_shipping_charge': 0,
        'estimated_delivery_days': 3,
        'shipping_zones': [],
        'enable_free_shipping': False,
    },
    'payment': {
        'accepted_cards': [],
        'cod_enabled': True,
        'online_payment_enabled': False,
        'bkash_enabled': False,
        'nagad_enabled': False,
        'rocket_enabled': False,
        'bkash_number': '',
        'nagad_number': '',
        'rocket_number': '',
    },
    'email': {
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_username': '',
        'smtp_password': '',
        'smtp_use_tls': True,
        'from_email': '',
        'order_notification_emails': [],
    },
    'notification': {
        'email_notifications': True,
        'order_confirmation': True,
        'order_shipped': True,
        'order_delivered': True,
        'new_order_admin': True,
        'low_stock_alert': True,
        'low_stock_threshold': 10,
        'new_customer_signup': True,
    },
}
