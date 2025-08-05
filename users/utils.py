import random
import string
from datetime import datetime, timedelta
from .models import OTP, User

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_to_phone(user, otp):
    """
    Send OTP to the user's phone number.
    This is a placeholder function - replace with actual SMS sending logic.
    """
    # Example SMS API placeholder
    print(f"Sending OTP '{otp}' to {user.full_phone}")
    
    # Replace with actual implementation:
    # from twilio.rest import Client
    # client = Client(account_sid, auth_token)
    # message = client.messages.create(
    #     body=f'Your OTP is: {otp}',
    #     from_='+1234567890',
    #     to=user.full_phone
    # )
    
    return True  # Simulate successful SMS send

def create_and_send_otp(user):
    """Create an OTP for the user and send it to their phone"""
    otp_code = generate_otp()

    # Optional: Set expiry (e.g., 5 minutes)
    expires_at = datetime.now() + timedelta(minutes=5)
    
    # Save OTP to the database
    OTP.objects.create(user=user, otp=otp_code, expires_at=expires_at)
    
    # Send OTP
    return send_otp_to_phone(user, otp_code)

def get_or_create_user(country_code, phone_number):
    """Get existing user or create a new one with the given phone number"""
    user, created = User.objects.get_or_create(
        country_code=country_code,
        phone_number=phone_number
    )
    return user
