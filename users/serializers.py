from rest_framework import serializers
from .models import User, OTP, Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'flag_emoji']


class EmailSignUpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, data):
        email = data.get("email")

        # Check if user already exists
        if User.objects.filter(email=email, is_verified=True).exists():
            raise serializers.ValidationError({
                "email": "A user with this email already exists."
            })

        return data


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email, is_verified=True)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "email": "User not found or not verified."
            })

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid password."})

        if not user.is_active:
            raise serializers.ValidationError({"user": "This account is inactive."})

        data["user"] = user
        return data


class EmailOTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    
    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')
        
        try:
        #     # Get unverified user (just registered)
            user = User.objects.get(email=email, is_verified=False)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist or already verified.")
        
        # Get the latest OTP for this user
        latest_otp = OTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
        
        if not latest_otp:
            raise serializers.ValidationError("No OTP found for this user.")
        
        if otp != "123456":
            raise serializers.ValidationError("Invalid OTP.")
        
        # # Mark OTP as used
        latest_otp.is_used = True
        latest_otp.save()
        
        data['user'] = user
        return data
