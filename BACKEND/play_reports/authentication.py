import os
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

class LookerStudioKeyAuthentication(BaseAuthentication):
    """
    Authentification simple basée sur une clé API statique définie dans les variables d'environnement.
    Le client doit envoyer la clé dans l'en-tête 'X-API-KEY'.
    """
    def authenticate(self, request):
        # La clé que le client doit envoyer, récupérée depuis l'en-tête X-API-KEY
        api_key_header = request.META.get('HTTP_X_API_KEY')
        
        # La clé secrète attendue, stockée sur le serveur dans les variables d'environnement
        secret_key = os.getenv('LOOKER_STUDIO_API_KEY')

        if not secret_key:
            # Mesure de sécurité : si la clé n'est pas configurée sur le serveur, personne ne peut se connecter.
            raise AuthenticationFailed('La clé API n''est pas configurée sur le serveur.')

        if not api_key_header:
            # Le client n'a pas envoyé de clé. L'authentification échoue silencieusement.
            return None

        if api_key_header != secret_key:
            # La clé envoyée par le client est incorrecte.
            raise AuthenticationFailed('Clé API invalide.')

        # Si la clé est correcte, on authentifie la requête.
        # On peut retourner un utilisateur par défaut ou anonyme, car l'accès est accordé par la clé.
        try:
            # Utilisons le premier superutilisateur comme utilisateur par défaut pour la session
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                # S'il n'y a pas de superutilisateur, on en crée un temporaire en mémoire
                return (User(), None)
            return (user, None)
        except User.DoesNotExist:
            return (User(), None)
