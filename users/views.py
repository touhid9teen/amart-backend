from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import PhoneSignUpSerializer,PhoneLoginSerializer, OTPVerificationSerializer, CountrySerializer
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



class PhoneSignUpView(APIView):
    def post(self, request):
        serializer = PhoneSignUpSerializer(data=request.data)
        if serializer.is_valid():
            country_code = serializer.validated_data['country_code']
            phone_number = serializer.validated_data['phone_number']
            password = serializer.validated_data['password']


            print('hare -------------------------')
            # Create unverified user first
            user = User(
                country_code=country_code,
                phone_number=phone_number,
                is_verified=False,  # Mark as unverified
                is_active=True
            )
            user.set_password(password)
            user.save()

            # Now send OTP
            # temp_user_data = {
            #     "country_code": country_code,
            #     "phone_number": phone_number,
            #     "user": user  # Pass user object for OTP creation
            # }
            sms_response = create_and_send_otp(user)

            if sms_response["response"]["code"] == 200:
                return Response({
                    "success": True,
                    "message": "User created. OTP sent successfully for verification.",
                    "data": {
                        "country_code": country_code,
                        "phone_number": phone_number
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


class PhoneLoginView(APIView):
    def post(self, request):
        serializer = PhoneLoginSerializer(data=request.data)
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
                    "country_code": user.country_code,
                    "phone_number": user.phone_number
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Invalid credentials",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class OTPVerificationView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Mark user as verified
            user.is_verified = True
            user.save()

            return Response({
                "success": True,
                "message": "Phone number verified successfully. You can now login.",
                "data": {
                    "user_id": str(user.id),
                    "country_code": user.country_code,
                    "phone_number": user.phone_number,
                    "is_verified": True
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Invalid OTP data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

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