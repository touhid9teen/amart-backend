from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Order
from .serializers import OrderSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser

class OrderListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):

        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
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