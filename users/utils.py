import random
import string
from datetime import datetime, timedelta
from .models import OTP, User

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_to_phone(user, otp):
    """
    Send OTP to the user's phone number
    This is a placeholder function - replace with actual SMS sending logic
    using services like Twilio, Vonage, etc.
    """
    # In a real implementation, you would use an SMS service like:
    # from twilio.rest import Client
    # client = Client(account_sid, auth_token)
    # message = client.messages.create(
    #     body=f'Your OTP is: {otp}',
    #     from_='+1234567890',
    #     to=user.full_phone
    # )
    
print    return True

def create_and_send_otp(user):
    """Create an OTP for the user and send it to their phone"""
    otp_code = generate_otp()
    
    # Save OTP to database
    OTP.objects.create(user=user, otp=otp_code)
    
    # Send OTP to user's phone
    return send_otp_to_phone(user, otp_code)

def get_or_create_user(country_code, phone_number):
    """Get existing user or create a new one with the given phone number"""
    user, created = User.objects.get_or_create(
        country_code=country_code,
        phone_number=phone_number
    )
    return user
