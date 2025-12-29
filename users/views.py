from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import (
    EmailSignUpSerializer, EmailLoginSerializer, EmailOTPVerificationSerializer,
    CountrySerializer
)
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


# ===================== EMAIL AUTHENTICATION =====================

class EmailSignUpView(APIView):
    def post(self, request):
        serializer = EmailSignUpSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            first_name = serializer.validated_data.get('first_name', '')
            last_name = serializer.validated_data.get('last_name', '')

            # Create unverified user first
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_verified=False,  # Mark as unverified
                is_active=True
            )
            user.set_password(password)
            user.save()

            # Send OTP
            sms_response = create_and_send_otp(user)

            if sms_response["response"]["code"] == 200:
                return Response({
                    "success": True,
                    "message": "User created. OTP sent successfully for verification.",
                    "data": {
                        "email": email
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # If OTP fails, delete the user or mark for cleanup
                user.delete()
                return Response({
                    "success": False,
                    "message": "Failed to send OTP"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "success": False,
            "message": "Invalid data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EmailLoginView(APIView):
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate tokens
            access_token = token_generator(user)
            refresh_token = refresh_token_generator(user)

            return Response({
                "success": True,
                "message": "Login successful",
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user_id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Invalid credentials",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EmailOTPVerificationView(APIView):
    def post(self, request):
        serializer = EmailOTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Mark user as verified
            user.is_verified = True
            user.save()

            return Response({
                "success": True,
                "message": "Email verified successfully. You can now login.",
                "data": {
                    "user_id": str(user.id),
                    "email": user.email,
                    "is_verified": True
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Invalid OTP data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ===================== PHONE AUTHENTICATION (COMMENTED OUT FOR FUTURE USE) =====================

# class PhoneSignUpView(APIView):
#     def post(self, request):
#         from .serializers import PhoneSignUpSerializer
#         serializer = PhoneSignUpSerializer(data=request.data)
#         if serializer.is_valid():
#             country_code = serializer.validated_data['country_code']
#             phone_number = serializer.validated_data['phone_number']
#             password = serializer.validated_data['password']
#
#             print('hare -------------------------')
#             # Create unverified user first
#             user = User(
#                 country_code=country_code,
#                 phone_number=phone_number,
#                 is_verified=False,  # Mark as unverified
#                 is_active=True
#             )
#             user.set_password(password)
#             user.save()
#
#             # Now send OTP
#             sms_response = create_and_send_otp(user)
#
#             if sms_response["response"]["code"] == 200:
#                 return Response({
#                     "success": True,
#                     "message": "User created. OTP sent successfully for verification.",
#                     "data": {
#                         "country_code": country_code,
#                         "phone_number": phone_number
#                     }
#                 }, status=status.HTTP_201_CREATED)
#             else:
#                 # If OTP fails, delete the user or mark for cleanup
#                 user.delete()
#                 return Response({
#                     "success": False,
#                     "message": "Failed to send OTP"
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         return Response({
#             "success": False,
#             "message": "Invalid data",
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
#
#
# class PhoneLoginView(APIView):
#     def post(self, request):
#         from .serializers import PhoneLoginSerializer
#         serializer = PhoneLoginSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#
#             # Generate tokens
#             access_token = token_generator(user)
#             refresh_token = refresh_token_generator(user)
#
#             return Response({
#                 "success": True,
#                 "message": "Login successful",
#                 "data": {
#                     "access_token": access_token,
#                     "refresh_token": refresh_token,
#                     "user_id": str(user.id),
#                     "country_code": user.country_code,
#                     "phone_number": user.phone_number
#                 }
#             }, status=status.HTTP_200_OK)
#
#         return Response({
#             "success": False,
#             "message": "Invalid credentials",
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
#
#
# class OTPVerificationView(APIView):
#     def post(self, request):
#         from .serializers import OTPVerificationSerializer
#         serializer = OTPVerificationSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#             
#             # Mark user as verified
#             user.is_verified = True
#             user.save()
#
#             return Response({
#                 "success": True,
#                 "message": "Phone number verified successfully. You can now login.",
#                 "data": {
#                     "user_id": str(user.id),
#                     "country_code": user.country_code,
#                     "phone_number": user.phone_number,
#                     "is_verified": True
#                 }
#             }, status=status.HTTP_200_OK)
#
#         return Response({
#             "success": False,
#             "message": "Invalid OTP data",
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)

class TokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response({
                "success": False,
                "message": "Refresh token is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = verify_token(refresh_token)

            if not payload or not payload.get("is_refresh", False):
                return Response({
                    "success": False,
                    "message": "Invalid or non-refresh token."
                }, status=status.HTTP_401_UNAUTHORIZED)

            user_id = payload.get("id")
            user = User.objects.get(id=user_id)

            access_token = token_generator(user)
            new_refresh_token = refresh_token_generator(user)

            return Response({
                "success": True,
                "message": "Token refreshed successfully.",
                "data": {
                    "access_token": access_token,
                    "refresh_token": new_refresh_token
                }
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Internal server error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)