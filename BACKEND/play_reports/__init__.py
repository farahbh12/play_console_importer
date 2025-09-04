# play_reports app

def __getattr__(name):
    """Lazy load authentication classes to avoid circular imports."""
    if name in ('AsyncJWTAuthentication', 'LookerStudioKeyAuthentication'):
        from .authentication import (
            AsyncJWTAuthentication as _AsyncJWTAuthentication,
            LookerStudioKeyAuthentication as _LookerStudioKeyAuthentication
        )
        if name == 'AsyncJWTAuthentication':
            return _AsyncJWTAuthentication
        return _LookerStudioKeyAuthentication
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['AsyncJWTAuthentication', 'LookerStudioKeyAuthentication']
