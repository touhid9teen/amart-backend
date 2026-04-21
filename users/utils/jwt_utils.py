from datetime import timedelta
from django.utils import timezone
from django.conf import settings
import jwt

def token_generator(user):
    """Generate an access token for the user"""
    now = timezone.now()
    payload = {
        'iat': now,
        'exp': now + timedelta(hours=1),
        'type': 'access',
        'email': user.email,
        # 'country_code': '+880',
        'userId': str(user.id), 
        "role": getattr(user, "role", "user"), 
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def refresh_token_generator(user):
    """Generate a refresh token for the user"""
    now = timezone.now()
    payload = {
        'iat': now,
        'exp': now + timedelta(days=30),  # Refresh token valid for 7 days
        'email': user.email,
        'type': 'refresh',
        # 'country_code': user.country_code,
        'userId': str(user.id),  # Convert UUID to string for JWT
        'is_refresh': True,  # Flag to identify refresh tokens
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token: str, expected_type: str = "access") -> dict | None:
    """
    Decode and validate a token.
    Returns payload dict or None on any failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        # Reject wrong token type (e.g. refresh used as access)
        if payload.get("type") != expected_type:
            return None
        return payload

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
