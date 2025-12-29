from rest_framework import serializers
from .models import User, OTP, Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'flag_emoji']


# ===================== EMAIL AUTHENTICATION =====================

class EmailSignUpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)

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
            # Get unverified user (just registered)
            user = User.objects.get(email=email, is_verified=False)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist or already verified.")
        
        # Get the latest OTP for this user
        latest_otp = OTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
        
        if not latest_otp:
            raise serializers.ValidationError("No OTP found for this user.")
        
        if latest_otp.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")
        
        # Mark OTP as used
        latest_otp.is_used = True
        latest_otp.save()
        
        data['user'] = user
        return data


# ===================== PHONE AUTHENTICATION (COMMENTED OUT FOR FUTURE USE) =====================

# class PhoneSignUpSerializer(serializers.Serializer):
#     country_code = serializers.CharField(max_length=5)
#     phone_number = serializers.CharField(max_length=15)
#     password = serializers.CharField(min_length=6, write_only=True)
#
#     def validate(self, data):
#         country_code = data.get("country_code")
#         phone_number = data.get("phone_number")
#
#         # Normalize phone
#         if len(phone_number) == 10 and not phone_number.startswith("0"):
#             phone_number = "0" + phone_number
#         data["phone_number"] = "".join(filter(str.isdigit, phone_number))
#
#         # Check if user already exists
#         if User.objects.filter(
#             country_code=country_code, 
#             phone_number=data["phone_number"],
#             is_verified=True  # Only check verified users
#         ).exists():
#             raise serializers.ValidationError({
#                 "phone_number": "A user with this phone number already exists."
#             })
#
#         return data
#
#
# class PhoneLoginSerializer(serializers.Serializer):
#     country_code = serializers.CharField(max_length=5)
#     phone_number = serializers.CharField(max_length=15)
#     password = serializers.CharField(write_only=True)
#
#     def validate(self, data):
#         country_code = data.get("country_code")
#         phone_number = data.get("phone_number")
#         password = data.get("password")
#
#         # Normalize phone number
#         if len(phone_number) == 10 and not phone_number.startswith("0"):
#             phone_number = "0" + phone_number
#         phone_number = "".join(filter(str.isdigit, phone_number))
#
#         try:
#             user = User.objects.get(
#                 country_code=country_code, 
#                 phone_number=phone_number,
#                 is_verified=True  # Only allow verified users to login
#             )
#         except User.DoesNotExist:
#             raise serializers.ValidationError({
#                 "phone_number": "User not found or not verified."
#             })
#
#         if not user.check_password(password):
#             raise serializers.ValidationError({"password": "Invalid password."})
#
#         if not user.is_active:
#             raise serializers.ValidationError({"user": "This account is inactive."})
#
#         data["user"] = user
#         return data
#
#
# class OTPVerificationSerializer(serializers.Serializer):
#     country_code = serializers.CharField(max_length=5)
#     phone_number = serializers.CharField(max_length=15)
#     otp = serializers.CharField(max_length=6)
#     
#     def validate(self, data):
#         country_code = data.get('country_code')
#         phone_number = data.get('phone_number')
#         otp = data.get('otp')
#         
#         # Normalize phone number
#         if len(phone_number) == 10 and not phone_number.startswith('0'):
#             phone_number = '0' + phone_number
#         data['phone_number'] = ''.join(filter(str.isdigit, phone_number))
#         
#         try:
#             # Get unverified user (just registered)
#             user = User.objects.get(
#                 country_code=data['country_code'], 
#                 phone_number=data['phone_number'],
#                 is_verified=False
#             )
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User with this phone number does not exist or already verified.")
#         
#         # Get the latest OTP for this user
#         latest_otp = OTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
#         
#         if not latest_otp:
#             raise serializers.ValidationError("No OTP found for this user.")
#         
#         if latest_otp.otp != otp:
#             raise serializers.ValidationError("Invalid OTP.")
#         
#         # Mark OTP as used
#         latest_otp.is_used = True
#         latest_otp.save()
#         
#         data['user'] = user
#         return data
