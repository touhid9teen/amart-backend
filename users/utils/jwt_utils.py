from datetime import timedelta
from django.utils import timezone
from django.conf import settings
import jwt

def token_generator(user):
    """Generate an access token for the user"""
    exp = timezone.now() + timedelta(hours=1)
    payload = {
        'exp': exp,
        'phone_number': user.phone_number,
        'country_code': user.country_code,
        'id': str(user.id),  # Convert UUID to string for JWT
        'iat': timezone.now(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def refresh_token_generator(user):
    """Generate a refresh token for the user"""
    exp = timezone.now() + timedelta(days=30)
    payload = {
        'exp': exp,
        'phone_number': user.phone_number,
        'country_code': user.country_code,
        'id': str(user.id),  # Convert UUID to string for JWT
        'iat': timezone.now(),
        'is_refresh': True,  # Flag to identify refresh tokens
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    """Verify a token and return the payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
