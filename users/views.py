import json
import logging

from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
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
from rest_framework.permissions import AllowAny


User = get_user_model()
logger = logging.getLogger(__name__)


class AuthRequestDataMixin:
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    @staticmethod
    def _get_request_data(request):
        """
        Accept JSON bodies even when the client omits the Content-Type header.
        """
        if request.data:
            return request.data

        if not request.body:
            return request.data

        try:
            parsed_body = json.loads(request.body.decode("utf-8"))
        except (TypeError, ValueError, UnicodeDecodeError):
            return request.data

        return parsed_body if isinstance(parsed_body, dict) else request.data

class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows countries to be viewed.
    Used for populating country code dropdown.
    """
    queryset = Country.objects.filter(is_active=True).order_by('name')
    serializer_class = CountrySerializer


class EmailSignUpView(AuthRequestDataMixin, APIView):
    permission_classes = [AllowAny]
    throttle_scope = "signup"

    def post(self, request):
        request_data = self._get_request_data(request)
        logger.warning(
            "Signup request debug: content_type=%s request_data=%s raw_body=%s",
            request.content_type,
            request_data,
            request.body.decode("utf-8", errors="replace") if request.body else "",
        )
        serializer = EmailSignUpSerializer(data=request_data)

        if not serializer.is_valid():
            logger.warning("Signup validation failed with errors: %s", serializer.errors)
            return Response(
                {
                    "success": False,
                    "code": "SIGNUP_VALIDATION_ERROR",
                    "message": self._flatten_errors(serializer.errors),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        existing_unverified_user = serializer.validated_data.get("existing_unverified_user")

        try:
            user = self._get_or_create_user(
                email=email,
                password=password,
                existing_unverified_user=existing_unverified_user,
            )
        except Exception:
            logger.exception("Failed to create/update user during signup. Email: %s", email)
            return Response(
                {
                    "success": False,
                    "code": "SIGNUP_USER_ERROR",
                    "message": "Could not create your account. Please try again later.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            otp_response = create_and_send_otp(user)
        except Exception:
            logger.exception("OTP service raised an exception for email: %s", email)
            return Response(
                {
                    "success": False,
                    "code": "SIGNUP_OTP_SERVICE_ERROR",
                    "message": "Account created but we could not send the verification email. Please try again later.",
                    "data": {"email": email},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if otp_response.get("response", {}).get("code") != 200:
            otp_error = otp_response.get("response", {}).get("message", "Unknown OTP error")
            logger.warning("OTP delivery failed for email: %s — reason: %s", email, otp_error)
            return Response(
                {
                    "success": False,
                    "code": "SIGNUP_OTP_DELIVERY_FAILED",
                    "message": "Account created but the verification email could not be delivered. Please try again later.",
                    "data": {"email": email},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info("Signup successful, OTP sent. Email: %s", email)
        return Response(
            {
                "success": True,
                "code": "SIGNUP_SUCCESS",
                "message": "Account created. Please check your email for the verification code.",
                "data": {
                    "email": email,
                    "user_id": str(user.id),
                },
            },
            status=status.HTTP_201_CREATED,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _get_or_create_user(email: str, password: str, existing_unverified_user):
        """
        Returns an existing unverified user (with updated password)
        or creates a brand-new unverified user.
        """
        if existing_unverified_user:
            logger.info("Resending OTP to existing unverified user. Email: %s", email)
            existing_unverified_user.set_password(password)
            existing_unverified_user.save(update_fields=["password"])
            return existing_unverified_user

        user = User(
            email=email,
            first_name="",
            last_name="",
            is_verified=False,
            is_active=True,
        )
        user.set_password(password)
        user.save()
        logger.info("New user created. Email: %s", email)
        return user

    @staticmethod
    def _flatten_errors(errors: dict) -> str:
        """Return the first human-readable message from a serializer errors dict."""
        for field, messages in errors.items():
            if isinstance(messages, list) and messages:
                return str(messages[0])
            if isinstance(messages, str):
                return messages
        return "Validation failed."

  # your token utils

class EmailLoginView(AuthRequestDataMixin, APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"  # add LoginRateThrottle in settings

    def post(self, request):
        request_data = self._get_request_data(request)
        serializer = EmailLoginSerializer(data=request_data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "code": "AUTH_VALIDATION_ERROR",
                    "message": self._flatten_errors(serializer.errors),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = serializer.validated_data["user"]
            access_token = token_generator(user)
            refresh_token = refresh_token_generator(user)

            logger.info("User logged in: %s", user.email)

            return Response(
                {
                    "success": True,
                    "code": "AUTH_LOGIN_SUCCESS",
                    "message": "Login successful.",
                    "data": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user": {
                            "id": str(user.id),
                            "email": user.email,
                        },
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            logger.exception("Unexpected error during login for request: %s", request_data.get("email"))
            return Response(
                {
                    "success": False,
                    "code": "AUTH_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def _flatten_errors(errors: dict) -> str:
        """Return the first human-readable error message from the serializer errors dict."""
        for field, messages in errors.items():
            if isinstance(messages, list) and messages:
                return str(messages[0])
            if isinstance(messages, str):
                return messages
        return "Validation failed."




class EmailOTPVerificationView(AuthRequestDataMixin, APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp_verify"

    def post(self, request):
        request_data = self._get_request_data(request)
        serializer = EmailOTPVerificationSerializer(data=request_data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "code": "OTP_VALIDATION_ERROR",
                    "message": self._flatten_errors(serializer.errors),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = serializer.validated_data["user"]
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        except Exception:
            logger.exception(
                "Failed to mark user as verified. Email: %s",
                request_data.get("email"),
            )
            return Response(
                {
                    "success": False,
                    "code": "OTP_VERIFY_SERVER_ERROR",
                    "message": "Verification failed due to a server error. Please try again later.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info("Email verified successfully. Email: %s", user.email)
        return Response(
            {
                "success": True,
                "code": "OTP_VERIFY_SUCCESS",
                "message": "Email verified successfully. You can now log in.",
                "data": {
                    "user_id": str(user.id),
                    "email": user.email,
                    "is_verified": True,
                },
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _flatten_errors(errors: dict) -> str:
        """Return the first human-readable message from a serializer errors dict."""
        for field, messages in errors.items():
            if isinstance(messages, list) and messages:
                return str(messages[0])
            if isinstance(messages, str):
                return messages
        return "Validation failed."

class ResendOTPView(AuthRequestDataMixin, APIView):
    """
    Resend OTP to user's email.
    Useful when user didn't receive the initial OTP or it expired.
    """
    def post(self, request):
        request_data = self._get_request_data(request)
        email = request_data.get('email')
        
        if not email:
            return Response({
                "success": False,
                "message": "Email is required",
                "code": "AmrtRFlr5hnd"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find user by email
            user = User.objects.filter(email=email).first()
            
            if not user:
                return Response({
                    "success": False,
                    "message": "No account found with this email. Please sign up first.",
                    "code": "AmrtRFlr5hnd"
                }, status=status.HTTP_404_NOT_FOUND)
            
            if user.is_verified:
                return Response({
                    "success": False,
                    "code": "AmrtRFlr5hnd",
                    "message": "This account is already verified. Please login instead."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Send new OTP
            logger.info(f"📧 Resending OTP to: {email}")
            otp_response = create_and_send_otp(user)
            
            if otp_response["response"]["code"] == 200:
                return Response({
                    "success": True,
                    "message": "OTP has been resent to your email.",
                    "code": "AmrtRSu2hnd",
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
                    "code": "AmrtRFls5hnd",
                    "message": f"Failed to resend OTP: {error_msg}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"❌ Error resending OTP to {email}: {str(e)}")
            return Response({
                "success": False,
                "code": "AmrtRFls5hnd",

                "message": f"Error resending OTP: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TokenRefreshView(AuthRequestDataMixin, APIView):
    def post(self, request):
        request_data = self._get_request_data(request)
        refresh_token = request_data.get("refresh_token")

        if not refresh_token:
            return Response({
                "success": False,
                "message": "Refresh token is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = verify_token(refresh_token,'refresh')

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
