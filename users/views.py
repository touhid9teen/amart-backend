from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import PhoneLoginSerializer, OTPVerificationSerializer, CountrySerializer
from .utils import create_and_send_otp, get_or_create_user
from .models import Country
from .utils.jwt_utils import token_generator, refresh_token_generator, verify_token

User = get_user_model()

class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows countries to be viewed.
    Used for populating country code dropdown.
    """
    queryset = Country.objects.filter(is_active=True).order_by('name')
    serializer_class = CountrySerializer

class PhoneLoginView(APIView):
    """
    API endpoint for initiating phone login
    Sends OTP to the provided phone number
    """
    def post(self, request):
        serializer = PhoneLoginSerializer(data=request.data)
        if serializer.is_valid():
            country_code = serializer.validated_data['country_code']
            phone_number = serializer.validated_data['phone_number']
            
            # Get or create user with this phone number
            user = get_or_create_user(country_code, phone_number)
            
            # Generate and send OTP
            if create_and_send_otp(user):
                return Response({
                    'message': 'OTP sent successfully',
                    'country_code': country_code,
                    'phone_number': phone_number
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send OTP'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OTPVerificationView(APIView):
    """
    API endpoint for verifying OTP
    Returns JWT token upon successful verification
    """
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            country_code = serializer.validated_data['country_code']
            phone_number = serializer.validated_data['phone_number']
            
            try:
                user = User.objects.get(country_code=country_code, phone_number=phone_number)
                
                # Mark user as verified
                user.is_verified = True
                user.save()
                
                # Generate custom JWT tokens
                access_token = token_generator(user)
                refresh_token = refresh_token_generator(user)
                
                return Response({
                    'message': 'OTP verified successfully',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user_id': str(user.id),
                    'country_code': user.country_code,
                    'phone_number': user.phone_number
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': 'User with this phone number does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TokenRefreshView(APIView):
    """
    API endpoint for refreshing access tokens using a refresh token
    """
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # from .utils.jwt_utils import verify_token
            payload = verify_token(refresh_token)
            
            if not payload:
                return Response({
                    'error': 'Invalid or expired refresh token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if it's a refresh token
            if not payload.get('is_refresh', False):
                return Response({
                    'error': 'Token is not a refresh token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user_id = payload.get('id')
            
            try:
                user = User.objects.get(id=user_id)
                
                # Generate new tokens
                access_token = token_generator(user)
                new_refresh_token = refresh_token_generator(user)
                
                return Response({
                    'access_token': access_token,
                    'refresh_token': new_refresh_token
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
