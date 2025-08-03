from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Order
from .serializers import OrderSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)  # Set up logging

class OrderListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()

            try:
                send_mail(
                    subject="🛒 New Order Received",
                    message=f"A new order has been placed. Order ID: {order.id} and order details: {order}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=settings.recipient_emails,
                    fail_silently=False,
                )
            except Exception as e:
                # Log the error but don't stop order creation
                logger.error(f"Failed to send order notification email: {e}")

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        order = get_object_or_404(Order, order_id=id, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

class UserOrderDetailListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)

class ApproveOrderAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, id):
        order = get_object_or_404(Order, order_id=id)
        if order.status == "approved":
            return Response({"detail": "Order is already approved."}, status=status.HTTP_400_BAD_REQUEST)
        order.status = "approved"
        order.save()
        return Response({"detail": "Order approved successfully."}, status=status.HTTP_200_OK)