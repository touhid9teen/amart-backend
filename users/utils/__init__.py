from .jwt_utils import token_generator, refresh_token_generator, verify_token
from .sms_utils import send_sms
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import random
import string
import logging
from ..models import OTP, User

logger = logging.getLogger(__name__)

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_to_email(user, otp):
    """
    Send OTP to the user's email address via admin email.
    
    Args:
        user: User object
        otp: OTP code to send
        
    Returns:
        dict: Response with status code and message
    """
    subject = "🔐 Amart Email Verification Code"
    
    # Plain text message
    plain_message = f"""
    Your Amart verification code is: {otp}
    
    This code will expire in 1 minutes.
    
    User Email: {user.email}
    
    Do not share this code with anyone.
    """
    
    # HTML email template
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 20px; border-radius: 8px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #2ecc71; margin: 0;">Amart Verification</h2>
            </div>
            
            <div style="background-color: white; padding: 20px; border-radius: 6px; border-left: 4px solid #2ecc71;">
                <p>Hello,</p>
                <p>Your <strong>Amart verification code</strong> is:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="background-color: #2ecc71; color: white; padding: 15px 30px; border-radius: 6px; font-size: 28px; font-weight: bold; letter-spacing: 5px;">
                        {otp}
                    </div>
                </div>
                
                <p><strong>Code expires in: 1 minutes</strong></p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                
                <p><small style="color: #666;">
                    <strong>Registered Email:</strong> {user.email}<br>
                    <strong>Do not share this code</strong> with anyone. Amart staff will never ask for your verification code.
                </small></p>
                
                <p><small style="color: #999;">
                    If you didn't request this verification code, please ignore this email.
                </small></p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #999;">
                <p>&copy; 2026 Amart. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        # Create email with both plain text and HTML
        # Send OTP directly to the user's email address
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email],  # Send to user's email, not admin
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        logger.info(f"✅ OTP sent successfully to user: {user.email}")
        return {"response": {"code": 200, "message": "OTP sent successfully to email"}}
        
    except Exception as e:
        logger.error(f"❌ Error sending email to {user.email}: {str(e)}")
        return {"response": {"code": 500, "message": f"Failed to send email: {str(e)}"}}


def create_and_send_otp(user):
    """
    Create an OTP for the user and send it to their email.
    
    Args:
        user: User object
        
    Returns:
        dict: Response with status code and message
    """
    try:
        otp_code = generate_otp()
        logger.info(f"Generated OTP for {user.email}: {otp_code}")
        
        # Save OTP to database
        otp = OTP.objects.create(user=user, otp=otp_code)
        
        # Send OTP to user's email
        result = send_otp_to_email(user, otp_code)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in create_and_send_otp for {user.email}: {str(e)}")
        return {"response": {"code": 500, "message": f"Failed to create and send OTP: {str(e)}"}}


# Commented out phone-based OTP sending for future use
# def send_otp_to_phone(user, otp, request_id=None):
#     """Send OTP to the user's phone number"""
#     message = f"Amart Verification Code: {otp}."
#     return send_sms(user.full_phone, message, request_id, is_unicode=0)

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
