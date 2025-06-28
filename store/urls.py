from django.urls import path
from .views import (
    CategoryList, CategoryDetail,
    ProductList, ProductDetail,
    FeaturedProducts, ProductsByCategory, UserCartAPIView
)

urlpatterns = [
    # Category URLs
    path('categories/', CategoryList.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetail.as_view(), name='category-detail'),
    
    # Product URLs
    path('products/', ProductList.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetail.as_view(), name='product-detail'),
    path('products/featured/', FeaturedProducts.as_view(), name='featured-products'),
    path('products/category/<slug:slug>/', ProductsByCategory.as_view(), name='products-by-category'),

    # Cart URLs
    path('user-cart/', UserCartAPIView.as_view(), name='user-cart'),                 # GET, POST, DELETE (all)
    path('user-cart/<int:pk>/', UserCartAPIView.as_view(), name='user-cart-detail'), # DELETE (single)
]

    