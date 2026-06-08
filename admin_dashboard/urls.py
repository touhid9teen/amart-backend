from django.urls import path
from admin_dashboard.views import (
    AdminLoginView,
    AdminProfileView,
    AdminTokenRefreshView,
    AdminBrandList,
    AdminBrandDetail,
    AdminCategoryList,
    AdminCategoryDetail,
    AdminProductList,
    AdminProductDetail,
    AdminProductDuplicate,
    AdminOrderList,
    AdminOrderDetail,
    AdminOrderStatusUpdate,
    AdminCustomerList,
    AdminCustomerDetail,
    AdminCustomerBlock,
    AdminCustomerUnblock,
    AdminReviewList,
    AdminReviewApprove,
    AdminReviewReject,
    AdminReviewDelete,
    AdminCouponList,
    AdminCouponDetail,
    AdminInventoryList,
    AdminInventoryItemDetail,
    AdminInventoryAdjust,
    AdminDashboardStats,
    AdminSalesTrend,
    AdminTopProducts,
    AdminRevenueData,
    AdminStoreSettingsView,
    AdminTaxSettingsView,
    AdminShippingSettingsView,
    AdminPaymentSettingsView,
    AdminEmailSettingsView,
    AdminNotificationSettingsView,
)

urlpatterns = [
    # ─── Auth ────────────────────────────────────────
    path('auth/login/', AdminLoginView.as_view(), name='admin-auth-login'),
    path('auth/profile/', AdminProfileView.as_view(), name='admin-auth-profile'),
    path('auth/refresh/', AdminTokenRefreshView.as_view(), name='admin-auth-refresh'),

    # ─── Brands ─────────────────────────────────────
    path('brands/', AdminBrandList.as_view(), name='admin-brand-list'),
    path('brands/<int:pk>/', AdminBrandDetail.as_view(), name='admin-brand-detail'),

    # ─── Categories ─────────────────────────────────
    path('categories/', AdminCategoryList.as_view(), name='admin-category-list'),
    path('categories/<int:pk>/', AdminCategoryDetail.as_view(), name='admin-category-detail'),

    # ─── Products ───────────────────────────────────
    path('products/', AdminProductList.as_view(), name='admin-product-list'),
    path('products/<int:pk>/', AdminProductDetail.as_view(), name='admin-product-detail'),
    path('products/<int:pk>/duplicate/', AdminProductDuplicate.as_view(), name='admin-product-duplicate'),

    # ─── Orders ─────────────────────────────────────
    path('orders/', AdminOrderList.as_view(), name='admin-order-list'),
    path('orders/<int:pk>/', AdminOrderDetail.as_view(), name='admin-order-detail'),
    path('orders/<int:pk>/status/', AdminOrderStatusUpdate.as_view(), name='admin-order-status'),

    # ─── Customers ──────────────────────────────────
    path('customers/', AdminCustomerList.as_view(), name='admin-customer-list'),
    path('customers/<uuid:pk>/', AdminCustomerDetail.as_view(), name='admin-customer-detail'),
    path('customers/<uuid:pk>/block/', AdminCustomerBlock.as_view(), name='admin-customer-block'),
    path('customers/<uuid:pk>/unblock/', AdminCustomerUnblock.as_view(), name='admin-customer-unblock'),

    # ─── Reviews ────────────────────────────────────
    path('reviews/', AdminReviewList.as_view(), name='admin-review-list'),
    path('reviews/<int:pk>/approve/', AdminReviewApprove.as_view(), name='admin-review-approve'),
    path('reviews/<int:pk>/reject/', AdminReviewReject.as_view(), name='admin-review-reject'),
    path('reviews/<int:pk>/', AdminReviewDelete.as_view(), name='admin-review-delete'),

    # ─── Coupons ────────────────────────────────────
    path('coupons/', AdminCouponList.as_view(), name='admin-coupon-list'),
    path('coupons/<int:pk>/', AdminCouponDetail.as_view(), name='admin-coupon-detail'),

    # ─── Inventory ──────────────────────────────────
    path('inventory/', AdminInventoryList.as_view(), name='admin-inventory-list'),
    path('inventory/<int:pk>/', AdminInventoryItemDetail.as_view(), name='admin-inventory-item'),
    path('inventory/adjust/', AdminInventoryAdjust.as_view(), name='admin-inventory-adjust'),

    # ─── Analytics ──────────────────────────────────
    path('analytics/dashboard/', AdminDashboardStats.as_view(), name='admin-analytics-dashboard'),
    path('analytics/sales-trend/', AdminSalesTrend.as_view(), name='admin-analytics-sales-trend'),
    path('analytics/top-products/', AdminTopProducts.as_view(), name='admin-analytics-top-products'),
    path('analytics/revenue/', AdminRevenueData.as_view(), name='admin-analytics-revenue'),

    # ─── Settings ───────────────────────────────────
    path('settings/store/', AdminStoreSettingsView.as_view(), name='admin-settings-store'),
    path('settings/tax/', AdminTaxSettingsView.as_view(), name='admin-settings-tax'),
    path('settings/shipping/', AdminShippingSettingsView.as_view(), name='admin-settings-shipping'),
    path('settings/payment/', AdminPaymentSettingsView.as_view(), name='admin-settings-payment'),
    path('settings/email/', AdminEmailSettingsView.as_view(), name='admin-settings-email'),
    path('settings/notification/', AdminNotificationSettingsView.as_view(), name='admin-settings-notifications'),
]
