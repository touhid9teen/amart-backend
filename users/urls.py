from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmailLoginView, EmailSignUpView, EmailOTPVerificationView,
    CountryViewSet, TokenRefreshView
)

router = DefaultRouter()
router.register(r'countries', CountryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Email authentication endpoints
    path('email-login/', EmailLoginView.as_view(), name='email-login'),
    path('email-signup/', EmailSignUpView.as_view(), name='email-signup'),
    path('verify-otp/', EmailOTPVerificationView.as_view(), name='verify-email-otp'),
    path('refresh-token/', TokenRefreshView.as_view(), name='refresh-token'),
    
    # Phone authentication endpoints (commented out for future use)
    # path('phone-login/', PhoneLoginView.as_view(), name='phone-login'),
    # path('phone-signup/', PhoneSignUpView.as_view(), name='phone-signup'),
    # path('verify-phone-otp/', OTPVerificationView.as_view(), name='verify-phone-otp'),
]
