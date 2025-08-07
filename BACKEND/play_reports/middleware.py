# Ce fichier est nécessaire pour ajouter les en-têtes de sécurité COEP.
# Sans cela, Looker Studio bloquera les requêtes vers l'API.
class CoepMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Ces en-têtes sont requis par Looker Studio pour des raisons de sécurité.
        response['Cross-Origin-Embedder-Policy'] = 'credentialless' # Plus flexible que require-corp
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        return response
