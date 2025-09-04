import os
import logging
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property
from django.apps import apps
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# This will be set the first time get_user_model_lazy is called
_user_model = None

def get_user_model():
    """Get the user model in a way that works even during app loading."""
    global _user_model
    if _user_model is not None:
        return _user_model
        
    try:
        from django.contrib.auth import get_user_model as django_get_user_model
        _user_model = django_get_user_model()
        return _user_model
    except (RuntimeError, LookupError):
        # Fallback for when auth models aren't loaded yet or can't be found
        from django.conf import settings
        user_model = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
        _user_model = apps.get_model(user_model)
        return _user_model

def get_user_model_lazy():
    """Get the user model, initializing it if necessary."""
    return get_user_model()

class AsyncJWTAuthentication(JWTAuthentication):
    """
    An async-compatible JWT authentication class that works with Django's async views.
    """
    async def authenticate(self, request):
        """
        The `authenticate` method is overridden to provide async support.
        It's called by DRF's authentication system.
        """
        # Get the user model when needed
        User = get_user_model_lazy()
        
        # Get the token from the header
        header = await sync_to_async(self.get_header)(request)
        if header is None:
            return None

        # Get the raw token from the header
        raw_token = await sync_to_async(self.get_raw_token)(header)
        if raw_token is None:
            return None

        try:
            # Validate the token and get the user
            validated_token = await self.get_validated_token(raw_token)
            user = await self.get_user(validated_token)
            
            # Check if user is active
            if not user.is_active:
                raise AuthenticationFailed('User is inactive', code='user_inactive')
                
            return (user, validated_token)
            
        except TokenError as e:
            # Handle token validation errors
            raise AuthenticationFailed({
                'detail': str(e),
                'code': 'token_not_valid',
            })
        except Exception as e:
            # Handle any other errors
            raise AuthenticationFailed({
                'detail': f'Authentication failed: {str(e)}',
                'code': 'authentication_failed',
            })

    async def get_validated_token(self, raw_token):
        """
        Validates token and returns a validated token wrapper object.
        """
        try:
            # Create a new token instance using the raw token
            token = api_settings.TOKEN_BACKEND_CLASS(raw_token, None)
            
            # Validate the token
            token.check_exp()
            
            return token
            
        except Exception as e:
            raise InvalidToken({
                'detail': 'Token is invalid or expired',
                'code': 'token_not_valid',
            })
            
    async def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        # Get the user model when needed
        User = get_user_model_lazy()
        
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
            
            # Use sync_to_async to call the synchronous ORM methods
            user = await sync_to_async(
                lambda: User.objects.get(**{api_settings.USER_ID_FIELD: user_id}),
                thread_sensitive=True
            )()
            
            if not user.is_active:
                raise AuthenticationFailed('User is inactive', code='user_inactive')
                
            return user
            
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found', code='user_not_found')
        except Exception as e:
            raise AuthenticationFailed({
                'detail': f'Error retrieving user: {str(e)}',
                'code': 'user_retrieval_error',
            })

    @cached_property
    def user_model(self):
        return get_user_model()

class LookerStudioKeyAuthentication(BaseAuthentication):
    """
    Simple API key authentication for Looker Studio integration.
    The client must send the key in the 'Authorization: ApiKey <key>' header.
    """
    async def authenticate(self, request):
        # Get the authorization header
        auth_header = request.headers.get('Authorization')

        # Check if the header is present and formatted correctly
        if not auth_header or not auth_header.startswith('ApiKey '):
            return None

        # Extract the API key
        try:
            api_key = auth_header.split(' ')[1].strip()
            if not api_key:
                return None
        except IndexError:
            return None
            
        try:
            # Get the user model when needed
            User = get_user_model_lazy()
            
            # Look up the user by API key
            user = await sync_to_async(
                lambda: User.objects.filter(api_key=api_key, is_active=True).first(),
                thread_sensitive=True
            )()
            
            if user is None:
                return None
                
            return (user, None)
            
        except Exception as e:
            logger.error(f"Error in LookerStudioKeyAuthentication: {str(e)}")
            return None
