from .jwt_utils import token_generator, refresh_token_generator, verify_token
from .sms_utils import send_sms
from django.core.mail import send_mail
from django.conf import settings

import random
import string
from ..models import OTP, User

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_to_email(user, otp):
    """Send OTP to the user's email address"""
    subject = "Amart Email Verification Code"
    message = f"Your Amart verification code is: {otp}\n\nUser Email: {user.email}\n\nDo not share this code with anyone."
    
    try:
        send_mail(
            subject,
            message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=settings.RECIPIENT_EMAILS,
            fail_silently=False,
        )
        return {"response": {"code": 200, "message": "OTP sent successfully to email"}}
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return {"response": {"code": 500, "message": f"Failed to send email: {str(e)}"}}

# Commented out phone-based OTP sending for future use
# def send_otp_to_phone(user, otp, request_id=None):
#     """Send OTP to the user's phone number"""
#     message = f"Amart Verification Code: {otp}."
#     return send_sms(user.full_phone, message, request_id, is_unicode=0)

def create_and_send_otp(user):
    """Create an OTP for the user and send it to their email"""
    otp_code = generate_otp()

    print(f"Generated OTP for {user.email}: {otp_code}")  # Debugging line
    # Save OTP to database
    otp = OTP.objects.create(user=user, otp=otp_code)
    
    # Send OTP to user's email
    return send_otp_to_email(user, otp_code)

# Commented out phone-based user creation for future use
# def get_or_create_user(country_code, phone_number):
#     """Get existing user or create a new one with the given phone number"""
#     try:
#         # First try to find by exact country_code and phone_number
#         user = User.objects.get(
#             country_code=country_code,
#             phone_number=phone_number
#         )
#         return user
#     except User.DoesNotExist:
#         # If not found, check if phone_number exists with different country_code
#         if User.objects.filter(phone_number=phone_number).exists():
#             # Handle the conflict - in this case we'll raise an exception
#             # You could also update the existing user's country_code instead
#             raise ValueError(f"Phone number {phone_number} already exists with a different country code")
#         
#         # Create new user if no conflicts
#         user = User.objects.create(
#             country_code=country_code,
#             phone_number=phone_number
#         )
#         return user
