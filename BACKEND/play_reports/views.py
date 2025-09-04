from django.http import JsonResponse
from django.views import View

class HealthCheckView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'ok',
            'message': 'Server is running',
            'version': '1.0.0'
        })
