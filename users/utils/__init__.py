from .jwt_utils import token_generator, refresh_token_generator, verify_token
from .sms_utils import send_sms

import random
import string
from ..models import OTP, User

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_to_phone(user, otp):
    """Send OTP to the user's phone number"""
    message = f"Your verification code is: {otp}"
    return send_sms(user.full_phone, message)

def create_and_send_otp(user):
    """Create an OTP for the user and send it to their phone"""
    otp_code = generate_otp()
    
    # Save OTP to database
    OTP.objects.create(user=user, otp=otp_code)
    
    # Send OTP to user's phone
    return send_otp_to_phone(user, otp_code)

def get_or_create_user(country_code, phone_number):
    """Get existing user or create a new one with the given phone number"""
    try:
        # First try to find by exact country_code and phone_number
        user = User.objects.get(
            country_code=country_code,
            phone_number=phone_number
        )
        return user
    except User.DoesNotExist:
        # If not found, check if phone_number exists with different country_code
        if User.objects.filter(phone_number=phone_number).exists():
            # Handle the conflict - in this case we'll raise an exception
            # You could also update the existing user's country_code instead
            raise ValueError(f"Phone number {phone_number} already exists with a different country code")
        
        # Create new user if no conflicts
        user = User.objects.create(
            country_code=country_code,
            phone_number=phone_number
        )
        return user
