from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import (
    EmailSignUpSerializer, EmailLoginSerializer, EmailOTPVerificationSerializer,
    CountrySerializer
)
from .utils import create_and_send_otp
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


class EmailSignUpView(APIView):
    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        serializer = EmailSignUpSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                # Check if user already exists
                existing_user = User.objects.filter(email=email).first()
                
                if existing_user:
                    if existing_user.is_verified:
                        # User already exists and is verified
                        return Response({
                            "success": False,
                            "message": "An account with this email already exists. Please login instead."
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        # User exists but not verified - update password and resend OTP
                        logger.info(f"ℹ️  User exists but not verified: {email}. Updating password and resending OTP.")
                        existing_user.set_password(password)
                        existing_user.save()
                        user = existing_user
                else:
                    # Create new unverified user
                    user = User(
                        email=email,
                        first_name='',  # Can be updated later by user
                        last_name='',   # Can be updated later by user
                        is_verified=False,  # Mark as unverified
                        is_active=True
                    )
                    user.set_password(password)
                    user.save()
                    logger.info(f"✅ User created: {email}")

                # Send OTP via email
                # Send OTP via email
                otp_response = create_and_send_otp(user)
                # otp_response = {"response": {"code": 200, "message": "OTP sent successfully via Resend"}}
                logger.info(f"OTP Response for {email}: {otp_response}")

                if otp_response["response"]["code"] == 200:
                    return Response({
                        "success": True,
                        "message": "User created. OTP sent successfully to your email for verification.",
                        "data": {
                            "email": email,
                            "user_id": str(user.id)
                        }
                    }, status=status.HTTP_201_CREATED)
                else:
                    # If OTP fails, keep the user but mark as unverified
                    logger.warning(f"⚠️  OTP sending failed for {email}: {otp_response['response'].get('message', 'Unknown error')}")
                    logger.warning(f"⚠️  User kept in database as unverified. User can retry OTP.")
                    
                    # User remains in database with is_verified=False
                    # Return the specific error message from OTP sending
                    error_msg = otp_response["response"].get("message", "Failed to send OTP")
                    return Response({
                        "success": False,
                        "message": f"{error_msg}. Your account has been created but not verified. Please contact support or try again later.",
                        "data": {
                            "email": email,
                            "user_id": str(user.id),
                            "is_verified": False
                        }
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as e:
                logger.error(f"❌ Error during signup for {email}: {str(e)}")
                    
                return Response({
                    "success": False,
                    "message": f"Signup failed: {str(e)}"
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


class ResendOTPView(APIView):
    """
    Resend OTP to user's email.
    Useful when user didn't receive the initial OTP or it expired.
    """
    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        email = request.data.get('email')
        
        if not email:
            return Response({
                "success": False,
                "message": "Email is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find user by email
            user = User.objects.filter(email=email).first()
            
            if not user:
                return Response({
                    "success": False,
                    "message": "No account found with this email. Please sign up first."
                }, status=status.HTTP_404_NOT_FOUND)
            
            if user.is_verified:
                return Response({
                    "success": False,
                    "message": "This account is already verified. Please login instead."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Send new OTP
            logger.info(f"📧 Resending OTP to: {email}")
            otp_response = create_and_send_otp(user)
            
            if otp_response["response"]["code"] == 200:
                return Response({
                    "success": True,
                    "message": "OTP has been resent to your email.",
                    "data": {
                        "email": email,
                        "user_id": str(user.id)
                    }
                }, status=status.HTTP_200_OK)
            else:
                error_msg = otp_response["response"].get("message", "Failed to send OTP")
                logger.error(f"❌ Failed to resend OTP to {email}: {error_msg}")
                return Response({
                    "success": False,
                    "message": f"Failed to resend OTP: {error_msg}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"❌ Error resending OTP to {email}: {str(e)}")
            return Response({
                "success": False,
                "message": f"Error resending OTP: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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