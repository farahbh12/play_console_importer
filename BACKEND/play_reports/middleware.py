from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(MiddlewareMixin):
    """
    Middleware personnalisé pour gérer l'authentification JWT.
    Vérifie et authentifie l'utilisateur via le token JWT dans l'en-tête Authorization.
    """
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self._async_capable = True
        self.jwt_authentication = JWTAuthentication()

    def process_request(self, request):
        """Traite la requête pour l'authentification JWT."""
        # Ne pas vérifier l'authentification pour les routes publiques
        public_paths = ['/token', '/token/refresh', '/token/verify', 
                       '/client/register', '/employee/register', 
                       '/password-reset', '/client/login', '/employee/login',
                       '/password-reset-confirm']
        
        # Normalize the path by removing any trailing slashes for comparison
        path = request.path_info.rstrip('/')
        
        # Check if the normalized path matches any public path (with or without trailing slash)
        if any(path == p.rstrip('/') for p in public_paths) or path.startswith('/password-reset-confirm/'):
            return None

        # Vérifier le token JWT
        try:
            # Tenter d'authentifier l'utilisateur via JWT
            auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
            
            if len(auth_header) == 2 and auth_header[0].lower() in ('bearer', 'jwt'):
                # Extraire le token
                token = auth_header[1]
                # Valider le token et récupérer l'utilisateur
                user_auth = self.jwt_authentication.authenticate(request)
                if user_auth is not None:
                    user, _ = user_auth
                    request.user = user
                    
                    # Charger le profil employé s'il existe
                    try:
                        from play_reports.models.employee import Employee
                        employee = Employee.objects.filter(user=user).first()
                        if employee:
                            user.employee_profile = employee
                    except Exception as e:
                        logger.warning(f'Error loading employee profile: {str(e)}')
                    
                    request._dont_enforce_csrf_checks = True
            
        except AuthenticationFailed as e:
            logger.warning(f'JWT Authentication failed: {str(e)}')
            from django.http import JsonResponse
            return JsonResponse(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f'Error in JWTAuthMiddleware: {str(e)}', exc_info=True)
            from django.http import JsonResponse
            return JsonResponse(
                {'detail': 'Authentication error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return None

    def process_response(self, request, response):
        """Traite la réponse pour ajouter des en-têtes CORS si nécessaire."""
        # Ajouter les en-têtes CORS
        response['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        return response

class CoepMiddleware(MiddlewareMixin):
    """
    Middleware to add COOP/COEP headers required by Looker Studio.
    """
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self._async_capable = True

    def process_response(self, request, response):
        """Add security headers to the response."""
        # These headers are required by Looker Studio for security reasons
        response['Cross-Origin-Embedder-Policy'] = 'credentialless'  # More flexible than require-corp
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        return response
