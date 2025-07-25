from rest_framework import serializers
from .models import User, OTP, Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'flag_emoji']

class PhoneLoginSerializer(serializers.Serializer):
    country_code = serializers.CharField(max_length=5)
    phone_number = serializers.CharField(max_length=15)
    
    def validate(self, data):
        country_code = data.get('country_code')
        phone_number = data.get('phone_number')
        
        # Ensure country code exists in our database
        # if not Country.objects.filter(code=country_code, is_active=True).exists():
        #     raise serializers.ValidationError({"country_code": "Invalid country code."})
        
          # If phone number is 10 digits and does not start with '0', add '0' at the start
        if len(phone_number) == 10 and not phone_number.startswith('0'):
            phone_number = '0' + phone_number
            
        # Remove any non-digit characters from phone number
        data['phone_number'] = ''.join(filter(str.isdigit, phone_number))
        
        return data

class OTPVerificationSerializer(serializers.Serializer):
    country_code = serializers.CharField(max_length=5)
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    
    def validate(self, data):
        country_code = data.get('country_code')
        phone_number = data.get('phone_number')
        otp = data.get('otp')
        
<<<<<<< HEAD
        # Ensure country code exists in our database
        # if not Country.objects.filter(code=country_code, is_active=True).exists():
        #     raise serializers.ValidationError({"country_code": "Invalid country code."})
=======
  
>>>>>>> b4a59b46ff485be444272926d3d01b18d9b6005b
        
        # Remove any non-digit characters from phone number
        data['phone_number'] = ''.join(filter(str.isdigit, phone_number))
        
        try:
            user = User.objects.get(country_code=data['country_code'], phone_number=data['phone_number'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this phone number does not exist.")
        
        # Get the latest OTP for this user
        latest_otp = OTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
        
        if not latest_otp:
            raise serializers.ValidationError("No OTP found for this user.")
        
        if latest_otp.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")
        
        # Mark OTP as used
        latest_otp.is_used = True
        latest_otp.save()
        
        return data
