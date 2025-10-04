from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PhoneLoginView,PhoneSignUpView, OTPVerificationView, CountryViewSet, TokenRefreshView

router = DefaultRouter()
router.register(r'countries', CountryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('phone-login/', PhoneLoginView.as_view(), name='phone-login'),
    path('phone-signup/', PhoneSignUpView.as_view(), name='phone-signup'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify-otp'),
    path('refresh-token/', TokenRefreshView.as_view(), name='refresh-token'),
]
