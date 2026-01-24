from .jwt_utils import token_generator, refresh_token_generator, verify_token
from .sms_utils import send_sms
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import random
import string
import logging
import os
from ..models import OTP, User

logger = logging.getLogger(__name__)

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))


def send_via_sendgrid(user, subject, plain_message, html_message):
    """Helper to send email via SendGrid API"""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        api_key = getattr(settings, 'SENDGRID_API_KEY', None) or os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.warning("SendGrid API key not found")
            return False
            
        message = Mail(
            from_email=settings.EMAIL_HOST_USER,
            to_emails=user.email,
            subject=subject,
            html_content=html_message)
            
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"✅ Email sent via SendGrid to {user.email}")
            return True
        else:
            logger.error(f"SendGrid failed with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"SendGrid error: {str(e)}")
        return False

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
    
    This code will expire in 5 minutes.
    
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
                
                <p><strong>Code expires in: 5 minutes</strong></p>
                
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
        # Priority 1: Try SendGrid if API Key exists (more reliable on Render)
        sendgrid_key = getattr(settings, 'SENDGRID_API_KEY', None) or os.environ.get('SENDGRID_API_KEY')
        if sendgrid_key:
            logger.info("Attempting to send via SendGrid...")
            if send_via_sendgrid(user, subject, plain_message, html_message):
                return {"response": {"code": 200, "message": "OTP sent successfully via SendGrid"}}

        # Priority 2: Fallback to SMTP
        
        # Validate email configuration
        if not settings.EMAIL_HOST_USER:
            logger.error("❌ EMAIL_HOST_USER is not configured")
            return {"response": {"code": 500, "message": "Email configuration error: EMAIL_HOST_USER not set"}}
        
        # Create email with both plain text and HTML
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        
        # Send email with detailed error logging
        email.send(fail_silently=False)
        logger.info(f"✅ OTP sent successfully via SMTP to user: {user.email}")
        return {"response": {"code": 200, "message": "OTP sent successfully to email"}}
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"❌ Error sending email to {user.email}: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        
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
