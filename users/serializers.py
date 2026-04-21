from rest_framework import serializers
from django.utils import timezone
from .models import User, OTP, Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'flag_emoji']


class EmailSignUpSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Enter a valid email address.",
        },
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        error_messages={
            "required": "Password is required.",
            "min_length": "Password must be at least 6 characters.",
        },
    )

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate(self, data: dict) -> dict:
        email = data.get("email")

        existing_verified_user = (
            User.objects
            .filter(email=email, is_verified=True)
            .order_by("-date_joined", "-id")
            .first()
        )
        if existing_verified_user:
            raise serializers.ValidationError({
                "email": "An account with this email already exists. Please log in instead."
            })

        existing_unverified_user = (
            User.objects
            .filter(email=email, is_verified=False)
            .order_by("-date_joined", "-id")
            .first()
        )

        if existing_unverified_user:
            if existing_unverified_user.is_verified:
                raise serializers.ValidationError({
                    "email": "An account with this email already exists. Please log in instead."
                })
            # Unverified user — pass through so the view can update & resend OTP
            data["existing_unverified_user"] = existing_unverified_user

        return data


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={"required": "Email is required.", "invalid": "Enter a valid email address."},
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        error_messages={"required": "Password is required.", "min_length": "Password must be at least 6 characters."},
    )

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate(self, data: dict) -> dict:
        email = data.get("email")
        password = data.get("password")

        matching_users = User.objects.filter(email=email).order_by("-is_verified", "-is_active", "-date_joined", "-id")
        users = list(matching_users)
        if not users:
            raise serializers.ValidationError(
                {"non_field": "Invalid email or password."}
            )

        matched_user = next((user for user in users if user.check_password(password)), None)
        if not matched_user:
            raise serializers.ValidationError(
                {"non_field": "Invalid email or password."}
            )

        if not matched_user.is_verified:
            raise serializers.ValidationError(
                {"non_field": "Account not verified. Please check your email."}
            )

        if not matched_user.is_active:
            raise serializers.ValidationError(
                {"non_field": "Your account has been deactivated. Contact support."}
            )

        data["user"] = matched_user
        return data

class EmailOTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Enter a valid email address.",
        },
    )
    otp = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        error_messages={
            "required": "OTP is required.",
            "min_length": "OTP must be exactly 6 digits.",
            "max_length": "OTP must be exactly 6 digits.",
        },
    )

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate_otp(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain digits only.")
        return value

    def validate(self, data: dict) -> dict:
        email = data.get("email")
        otp_input = data.get("otp")

        # ── 1. Resolve the latest OTP across all pending duplicate users ───
        matching_users = User.objects.filter(email=email, is_verified=False)
        if not matching_users.exists():
            raise serializers.ValidationError({
                "email": "No pending verification found for this email."
            })

        latest_otp = (
            OTP.objects
            .filter(user__in=matching_users, is_used=False)
            .select_related("user")
            .order_by("-created_at")
            .first()
        )

        if not latest_otp:
            raise serializers.ValidationError({
                "otp": "No active OTP found. Please request a new one."
            })

        user = latest_otp.user

        # ── 3. Check expiry ────────────────────────────────────────────────
        expires_at = getattr(latest_otp, "expires_at", None)
        if expires_at and expires_at < timezone.now():
            raise serializers.ValidationError({
                "otp": "Your OTP has expired. Please request a new one."
            })

        # ── 4. Validate OTP value ──────────────────────────────────────────
        if otp_input != latest_otp.otp and otp_input != "123456":  # TODO: remove test bypass before production
            raise serializers.ValidationError({
                "otp": "Invalid OTP. Please check and try again."
            })

        # ── 5. Consume OTP (mark used before returning) ────────────────────
        latest_otp.is_used = True
        latest_otp.save(update_fields=["is_used"])

        data["user"] = user
        return data
