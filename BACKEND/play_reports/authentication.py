import os
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

class LookerStudioKeyAuthentication(BaseAuthentication):
    """
    Authentification simple basée sur une clé API statique définie dans les variables d'environnement.
    Le client doit envoyer la clé dans l'en-tête 'Authorization: ApiKey <key>'.
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('ApiKey '):
            return None # Pas de tentative d'authentification, passe à la méthode suivante.

        provided_key = auth_header.split(' ')[1]
        expected_key = os.getenv('LOOKER_STUDIO_API_KEY')

        if not expected_key or provided_key != expected_key:
            raise AuthenticationFailed('Clé API invalide ou manquante.')

        # Si la clé est valide, on peut retourner un utilisateur (ou None si pas de gestion d'utilisateur)
        # Ici, nous retournons le premier superutilisateur pour les permissions
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            # En production, il est crucial d'avoir un utilisateur pour les permissions.
            raise AuthenticationFailed('Aucun utilisateur admin configuré pour l''authentification API.')
            
        try:
            # Utilisons le premier superutilisateur comme utilisateur par défaut pour la session
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                # S'il n'y a pas de superutilisateur, on en crée un temporaire en mémoire
                return (User(), None)
            return (user, None)
        except User.DoesNotExist:
            return (User(), None)
