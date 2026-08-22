import json
import logging
from decimal import Decimal
from datetime import datetime, timedelta

from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from store.models import Category, Product
from order.models import Order, OrderItem
from admin_dashboard.models import Brand, Review, Coupon, InventoryLog, SystemSetting
from admin_dashboard.serializers import (
    AdminLoginSerializer,
    AdminProfileSerializer,
    BrandSerializer,
    AdminCategorySerializer,
    AdminCategoryListSerializer,
    AdminProductSerializer,
    AdminProductListSerializer,
    AdminOrderListSerializer,
    AdminOrderSerializer,
    OrderStatusUpdateSerializer,
    AdminCustomerListSerializer,
    AdminCustomerSerializer,
    AdminReviewListSerializer,
    CouponSerializer,
    AdminInventoryListSerializer,
    AdminInventoryItemSerializer,
    InventoryAdjustSerializer,
    SETTING_SERIALIZER_MAP,
    SETTING_DEFAULTS,
)
from users.utils.jwt_utils import token_generator, refresh_token_generator, verify_token

User = get_user_model()
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  HELPER: Admin Permission Check
# ──────────────────────────────────────────────

def is_admin_user(user):
    """Check if the user has admin role permissions."""
    return user.is_authenticated and (
        getattr(user, 'role', 'user') in ['admin', 'superadmin']
    )


class AdminPermissionMixin:
    """Mixin that checks admin role permissions."""

    def check_admin_permission(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"success": False, "code": "UNAUTHORIZED", "message": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not is_admin_user(request.user):
            return Response(
                {"success": False, "code": "FORBIDDEN", "message": "Admin access required."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None


def admin_required(view_func):
    """Decorator to check admin permissions on views."""
    def _wrapped_view(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"success": False, "code": "UNAUTHORIZED", "message": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not is_admin_user(request.user):
            return Response(
                {"success": False, "code": "FORBIDDEN", "message": "Admin access required."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return view_func(self, request, *args, **kwargs)
    return _wrapped_view


# ──────────────────────────────────────────────
#  AUTH VIEWS
# ──────────────────────────────────────────────

class AdminLoginView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        data = request.data if request.data else {}
        if not data and request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        serializer = AdminLoginSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "code": "ADMIN_AUTH_VALIDATION_ERROR",
                    "message": next(iter(serializer.errors.values()))[0]
                    if isinstance(next(iter(serializer.errors.values())), list)
                    else str(next(iter(serializer.errors.values()))),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data['user']
        access_token = token_generator(user)
        refresh_token = refresh_token_generator(user)

        logger.info(f"Admin login successful: {user.email}")

        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": {
                    "user": AdminProfileSerializer(user).data,
                    "tokens": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                },
            },
            status=status.HTTP_200_OK,
        )


class AdminProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin_user(request.user):
            return Response(
                {"success": False, "code": "FORBIDDEN", "message": "Admin access required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AdminProfileSerializer(request.user)
        return Response(
            {
                "success": True,
                "message": "Profile retrieved successfully.",
                "data": serializer.data,
            }
        )


class AdminTokenRefreshView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        data = request.data if request.data else {}
        if not data and request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        refresh_token = data.get('refresh_token')

        if not refresh_token:
            return Response(
                {"success": False, "message": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = verify_token(refresh_token, 'refresh')
            if not payload or not payload.get('is_refresh', False):
                return Response(
                    {"success": False, "message": "Invalid or non-refresh token."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user_id = payload.get('userId')
            if not user_id:
                return Response(
                    {"success": False, "message": "Invalid token payload."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user = User.objects.get(id=user_id)

            if not is_admin_user(user):
                return Response(
                    {"success": False, "message": "Admin access required."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            new_access_token = token_generator(user)
            new_refresh_token = refresh_token_generator(user)

            return Response(
                {
                    "success": True,
                    "message": "Token refreshed successfully.",
                    "data": {
                        "access_token": new_access_token,
                        "refresh_token": new_refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception("Token refresh error")
            return Response(
                {"success": False, "message": f"Internal server error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ──────────────────────────────────────────────
#  BRAND VIEWS
# ──────────────────────────────────────────────

class AdminBrandList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        brands = Brand.objects.all()
        search = request.query_params.get('search')
        if search:
            brands = brands.filter(name__icontains=search)

        serializer = BrandSerializer(brands, many=True)
        return Response(
            {"success": True, "message": "Brands retrieved successfully.", "data": serializer.data}
        )

    def post(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        serializer = BrandSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Brand created successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "message": "Validation failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AdminBrandDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Brand, pk=pk)

    def get(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        brand = self.get_object(pk)
        serializer = BrandSerializer(brand)
        return Response(
            {"success": True, "message": "Brand retrieved successfully.", "data": serializer.data}
        )

    def patch(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        brand = self.get_object(pk)
        serializer = BrandSerializer(brand, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Brand updated successfully.", "data": serializer.data}
            )
        return Response(
            {"success": False, "message": "Validation failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        brand = self.get_object(pk)
        brand.delete()
        return Response(
            {"success": True, "message": "Brand deleted successfully."},
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────
#  CATEGORY VIEWS
# ──────────────────────────────────────────────

class AdminCategoryList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        categories = Category.objects.all()
        search = request.query_params.get('search')
        if search:
            categories = categories.filter(name__icontains=search)

        serializer = AdminCategoryListSerializer(categories, many=True)
        return Response(
            {"success": True, "message": "Categories retrieved successfully.", "data": serializer.data}
        )

    def post(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        serializer = AdminCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Category created successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "message": "Validation failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AdminCategoryDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Category, pk=pk)

    def get(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        category = self.get_object(pk)
        serializer = AdminCategorySerializer(category)
        return Response(
            {"success": True, "message": "Category retrieved successfully.", "data": serializer.data}
        )

    def patch(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        category = self.get_object(pk)
        serializer = AdminCategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Category updated successfully.", "data": serializer.data}
            )
        return Response(
            {"success": False, "message": "Validation failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        category = self.get_object(pk)
        category.delete()
        return Response(
            {"success": True, "message": "Category deleted successfully."},
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────
#  PRODUCT VIEWS
# ──────────────────────────────────────────────

class AdminProductList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        products = Product.objects.select_related('brand').prefetch_related('categories').all()

        # Filters
        search = request.query_params.get('search')
        if search:
            products = products.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )

        category_id = request.query_params.get('category_id')
        if category_id:
            products = products.filter(categories__id=category_id)

        brand_id = request.query_params.get('brand_id')
        if brand_id:
            products = products.filter(brand_id=brand_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            products = products.filter(status=status_filter)

        is_featured = request.query_params.get('is_featured')
        if is_featured and is_featured.lower() == 'true':
            products = products.filter(is_featured=True)

        low_stock = request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            products = products.filter(stock__lte=10)

        products = products.distinct()
        serializer = AdminProductListSerializer(products, many=True)
        return Response(
            {"success": True, "message": "Products retrieved successfully.", "data": serializer.data}
        )

    def post(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        serializer = AdminProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Product created successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "message": "Validation failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AdminProductDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Product.objects.select_related('brand').prefetch_related('categories'), pk=pk)

    def get(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        product = self.get_object(pk)
        serializer = AdminProductSerializer(product)
        return Response(
            {"success": True, "message": "Product retrieved successfully.", "data": serializer.data}
        )

    def patch(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        product = self.get_object(pk)
        serializer = AdminProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Product updated successfully.", "data": serializer.data}
            )
        return Response(
            {"success": False, "message": "Validation failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        product = self.get_object(pk)
        product.delete()
        return Response(
            {"success": True, "message": "Product deleted successfully."},
            status=status.HTTP_200_OK,
        )


class AdminProductDuplicate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        original = get_object_or_404(Product, pk=pk)
        import uuid

        # Save category and brand references before modifying original
        category_ids = list(original.categories.values_list('id', flat=True))
        brand_id = original.brand_id
        tags = original.tags  # JSONField

        # Create a duplicate with new identity
        original.pk = None
        original.id = None
        original.name = f"{original.name} (Copy)"
        original.slug = f"copy-{uuid.uuid4().hex[:8]}"
        original.sku = None
        original.stock = 0
        original.status = 'draft'
        original.brand_id = brand_id
        original.tags = tags
        original.save()

        # Copy categories on the newly saved instance
        if category_ids:
            original.categories.set(category_ids)

        serializer = AdminProductSerializer(original)
        return Response(
            {"success": True, "message": "Product duplicated successfully.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────
#  ORDER VIEWS
# ──────────────────────────────────────────────

class AdminOrderList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        orders = Order.objects.all()

        # Filters
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)

        search = request.query_params.get('search')
        if search:
            orders = orders.filter(
                Q(order_id__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )

        date_from = request.query_params.get('date_from')
        if date_from:
            orders = orders.filter(created_at__gte=date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            orders = orders.filter(created_at__lte=date_to)

        orders = orders.order_by('-created_at')
        serializer = AdminOrderListSerializer(orders, many=True)
        return Response(
            {"success": True, "message": "Orders retrieved successfully.", "data": serializer.data}
        )


class AdminOrderDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        order = get_object_or_404(Order, pk=pk)
        serializer = AdminOrderSerializer(order)
        return Response(
            {"success": True, "message": "Order retrieved successfully.", "data": serializer.data}
        )


class AdminOrderStatusUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        order = get_object_or_404(Order, pk=pk)
        serializer = OrderStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid status.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = serializer.validated_data['status']
        order.save(update_fields=['status'])

        return Response(
            {
                "success": True,
                "message": f"Order status updated to '{order.get_status_display()}'.",
                "data": {"id": order.pk, "status": order.status},
            }
        )


# ──────────────────────────────────────────────
#  CUSTOMER VIEWS
# ──────────────────────────────────────────────

class AdminCustomerList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        customers = User.objects.filter(role='user')

        search = request.query_params.get('search')
        if search:
            customers = customers.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        is_active = request.query_params.get('is_active')
        if is_active:
            if is_active.lower() == 'true':
                customers = customers.filter(is_active=True)
            elif is_active.lower() == 'false':
                customers = customers.filter(is_active=False)

        customers = customers.order_by('-date_joined')
        serializer = AdminCustomerListSerializer(customers, many=True)
        return Response(
            {"success": True, "message": "Customers retrieved successfully.", "data": serializer.data}
        )


class AdminCustomerDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        customer = get_object_or_404(User, pk=pk, role='user')
        serializer = AdminCustomerSerializer(customer)
        return Response(
            {"success": True, "message": "Customer retrieved successfully.", "data": serializer.data}
        )

    def delete(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        customer = get_object_or_404(User, pk=pk, role='user')
        customer.delete()
        return Response(
            {"success": True, "message": "Customer deleted successfully."},
            status=status.HTTP_200_OK,
        )


class AdminCustomerBlock(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        customer = get_object_or_404(User, pk=pk, role='user')
        if not customer.is_active:
            return Response(
                {"success": True, "message": "Customer is already blocked."}
            )

        customer.is_active = False
        customer.save(update_fields=['is_active'])
        return Response(
            {"success": True, "message": "Customer blocked successfully."}
        )


class AdminCustomerUnblock(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        customer = get_object_or_404(User, pk=pk, role='user')
        if customer.is_active:
            return Response(
                {"success": True, "message": "Customer is already active."}
            )

        customer.is_active = True
        customer.save(update_fields=['is_active'])
        return Response(
            {"success": True, "message": "Customer unblocked successfully."}
        )


# ──────────────────────────────────────────────
#  REVIEW VIEWS
# ──────────────────────────────────────────────

class AdminReviewList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        reviews = Review.objects.all()

        status_filter = request.query_params.get('status')
        if status_filter:
            reviews = reviews.filter(status=status_filter)

        product_id = request.query_params.get('product_id')
        if product_id:
            reviews = reviews.filter(product_id=product_id)

        search = request.query_params.get('search')
        if search:
            reviews = reviews.filter(
                Q(comment__icontains=search) |
                Q(user__email__icontains=search)
            )

        reviews = reviews.order_by('-created_at')
        serializer = AdminReviewListSerializer(reviews, many=True)
        return Response(
            {"success": True, "message": "Reviews retrieved successfully.", "data": serializer.data}
        )


class AdminReviewApprove(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        review = get_object_or_404(Review, pk=pk)
        review.status = 'approved'
        review.save(update_fields=['status'])
        return Response(
            {"success": True, "message": "Review approved successfully."}
        )


class AdminReviewReject(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        review = get_object_or_404(Review, pk=pk)
        review.status = 'rejected'
        review.save(update_fields=['status'])
        return Response(
            {"success": True, "message": "Review rejected successfully."}
        )


class AdminReviewDelete(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        review = get_object_or_404(Review, pk=pk)
        review.delete()
        return Response(
            {"success": True, "message": "Review deleted successfully."},
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────
#  COUPON VIEWS
# ──────────────────────────────────────────────

class AdminCouponList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        coupons = Coupon.objects.all()

        search = request.query_params.get('search')
        if search:
            coupons = coupons.filter(code__icontains=search)

        is_active = request.query_params.get('is_active')
        if is_active:
            if is_active.lower() == 'true':
                coupons = coupons.filter(is_active=True)
            elif is_active.lower() == 'false':
                coupons = coupons.filter(is_active=False)

        coupons = coupons.order_by('-created_at')
        serializer = CouponSerializer(coupons, many=True)
        return Response(
            {"success": True, "message": "Coupons retrieved successfully.", "data": serializer.data}
        )

    def post(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        serializer = CouponSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Coupon created successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "message": "Validation failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AdminCouponDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Coupon, pk=pk)

    def get(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        coupon = self.get_object(pk)
        serializer = CouponSerializer(coupon)
        return Response(
            {"success": True, "message": "Coupon retrieved successfully.", "data": serializer.data}
        )

    def patch(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        coupon = self.get_object(pk)
        serializer = CouponSerializer(coupon, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Coupon updated successfully.", "data": serializer.data}
            )
        return Response(
            {"success": False, "message": "Validation failed.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        coupon = self.get_object(pk)
        coupon.delete()
        return Response(
            {"success": True, "message": "Coupon deleted successfully."},
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────
#  INVENTORY VIEWS
# ──────────────────────────────────────────────

class AdminInventoryList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        products = Product.objects.all()

        low_stock = request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            products = products.filter(stock__lte=10)

        search = request.query_params.get('search')
        if search:
            products = products.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )

        products = products.order_by('name')
        serializer = AdminInventoryListSerializer(products, many=True)
        return Response(
            {"success": True, "message": "Inventory retrieved successfully.", "data": serializer.data}
        )


class AdminInventoryItemDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        product = get_object_or_404(Product, pk=pk)
        serializer = AdminInventoryItemSerializer(product)

        # Include recent inventory logs
        logs = InventoryLog.objects.filter(product=product)[:20]
        log_data = [
            {
                "id": log.id,
                "quantity": log.quantity,
                "reason": log.reason,
                "created_at": log.created_at,
            }
            for log in logs
        ]

        data = serializer.data
        data['logs'] = log_data
        return Response(
            {"success": True, "message": "Inventory item retrieved successfully.", "data": data}
        )


class AdminInventoryAdjust(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        serializer = InventoryAdjustSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Validation failed.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        reason = serializer.validated_data['reason']

        product = Product.objects.get(id=product_id)
        product.stock = F('stock') + quantity
        product.save(update_fields=['stock'])
        product.refresh_from_db()

        # Log the adjustment
        InventoryLog.objects.create(
            product=product,
            quantity=quantity,
            reason=reason,
        )

        return Response(
            {
                "success": True,
                "message": "Stock adjusted successfully.",
                "data": {
                    "product_id": product.id,
                    "product_name": product.name,
                    "new_stock": product.stock,
                    "adjustment": quantity,
                },
            }
        )


# ──────────────────────────────────────────────
#  ANALYTICS VIEWS
# ──────────────────────────────────────────────

class AdminDashboardStats(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        this_month_start = today_start.replace(day=1)

        # Total counts
        total_products = Product.objects.count()
        total_categories = Category.objects.count()
        total_customers = User.objects.filter(role='user').count()
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        # Today's stats
        today_orders = Order.objects.filter(created_at__gte=today_start).count()
        today_revenue = Order.objects.filter(
            created_at__gte=today_start,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        # Monthly stats
        monthly_orders = Order.objects.filter(created_at__gte=this_month_start).count()
        monthly_revenue = Order.objects.filter(
            created_at__gte=this_month_start,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        # Orders by status
        orders_by_status = (
            Order.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        status_summary = {item['status']: item['count'] for item in orders_by_status}

        # Low stock products
        low_stock_count = Product.objects.filter(stock__lte=10).count()

        # Pending reviews
        pending_reviews = Review.objects.filter(status='pending').count()

        return Response(
            {
                "success": True,
                "message": "Dashboard stats retrieved successfully.",
                "data": {
                    "overview": {
                        "total_products": total_products,
                        "total_categories": total_categories,
                        "total_customers": total_customers,
                        "total_orders": total_orders,
                        "total_revenue": total_revenue,
                    },
                    "today": {
                        "orders": today_orders,
                        "revenue": today_revenue,
                    },
                    "this_month": {
                        "orders": monthly_orders,
                        "revenue": monthly_revenue,
                    },
                    "orders_by_status": status_summary,
                    "alerts": {
                        "low_stock_products": low_stock_count,
                        "pending_reviews": pending_reviews,
                    },
                },
            }
        )


class AdminSalesTrend(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        days = int(request.query_params.get('days', 30))

        start_date = timezone.now() - timedelta(days=days)

        sales_data = (
            Order.objects
            .filter(created_at__gte=start_date, status__in=['delivered', 'shipped', 'processing'])
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(
                total_orders=Count('id'),
                total_revenue=Sum('total_amount'),
                total_items=Sum('items__quantity'),
            )
            .order_by('date')
        )

        return Response(
            {
                "success": True,
                "message": "Sales trend retrieved successfully.",
                "data": list(sales_data),
            }
        )


class AdminTopProducts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        limit = int(request.query_params.get('limit', 10))
        days = int(request.query_params.get('days', 30))

        start_date = timezone.now() - timedelta(days=days)

        top_products = (
            OrderItem.objects
            .filter(order__created_at__gte=start_date)
            .values('product__id', 'product__name')
            .annotate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('product__sellingPice')),
            )
            .order_by('-total_quantity')[:limit]
        )

        data = [
            {
                "id": item['product__id'],
                "name": item['product__name'],
                "total_quantity": item['total_quantity'],
                "total_revenue": item['total_revenue'],
            }
            for item in top_products
        ]

        return Response(
            {
                "success": True,
                "message": "Top products retrieved successfully.",
                "data": data,
            }
        )


class AdminRevenueData(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        months = int(request.query_params.get('months', 12))

        start_date = timezone.now() - timedelta(days=months * 30)

        revenue_data = (
            Order.objects
            .filter(created_at__gte=start_date, status__in=['delivered', 'shipped', 'processing'])
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                revenue=Sum('total_amount'),
                orders=Count('id'),
            )
            .order_by('month')
        )

        data = [
            {
                "date": item['month'].strftime('%Y-%m') if item['month'] else None,
                "revenue": item['revenue'],
                "orders": item['orders'],
            }
            for item in revenue_data
        ]

        return Response(
            {
                "success": True,
                "message": "Revenue data retrieved successfully.",
                "data": data,
            }
        )


# ──────────────────────────────────────────────
#  SETTINGS VIEWS
# ──────────────────────────────────────────────

class BaseSettingsView(APIView):
    """Base view for settings CRUD operations."""
    permission_classes = [IsAuthenticated]
    settings_group = None  # Override in subclass

    def get_setting_group(self):
        if self.settings_group is None:
            raise NotImplementedError("settings_group must be defined")
        return self.settings_group

    def get_serializer_class(self):
        return SETTING_SERIALIZER_MAP.get(self.settings_group)

    def get(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        group = self.get_setting_group()
        serializer_class = self.get_serializer_class()

        try:
            setting = SystemSetting.objects.get(group=group)
            settings_data = setting.settings
        except SystemSetting.DoesNotExist:
            settings_data = SETTING_DEFAULTS.get(group, {})

        serializer = serializer_class(data=settings_data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                "success": True,
                "message": f"{group.title()} settings retrieved successfully.",
                "data": serializer.validated_data,
            }
        )

    def patch(self, request):
        permission_error = AdminPermissionMixin().check_admin_permission(request)
        if permission_error:
            return permission_error

        group = self.get_setting_group()
        serializer_class = self.get_serializer_class()

        serializer = serializer_class(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Validation failed.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        setting, created = SystemSetting.objects.update_or_create(
            group=group,
            defaults={'settings': serializer.validated_data},
        )

        return Response(
            {
                "success": True,
                "message": f"{group.title()} settings updated successfully.",
                "data": serializer.validated_data,
            }
        )


class AdminStoreSettingsView(BaseSettingsView):
    settings_group = 'store'


class AdminTaxSettingsView(BaseSettingsView):
    settings_group = 'tax'


class AdminShippingSettingsView(BaseSettingsView):
    settings_group = 'shipping'


class AdminPaymentSettingsView(BaseSettingsView):
    settings_group = 'payment'


class AdminEmailSettingsView(BaseSettingsView):
    settings_group = 'email'


class AdminNotificationSettingsView(BaseSettingsView):
    settings_group = 'notification'
