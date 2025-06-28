from django.urls import path
from .views import OrderListCreateAPIView, OrderDetailAPIView, UserOrderDetailListAPIView, ApproveOrderAPIView

urlpatterns = [
    path('orders/', OrderListCreateAPIView.as_view()),
    path('orders/<uuid:id>/', OrderDetailAPIView.as_view()),
    path('orders/user/all/', UserOrderDetailListAPIView.as_view()),
    path('orders/<uuid:id>/approve/', ApproveOrderAPIView.as_view()),
]