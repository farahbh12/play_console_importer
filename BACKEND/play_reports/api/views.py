from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny
from django.apps import apps

# Dictionnaire pour mapper les noms de rapports aux modèles
# Le nom du rapport (clé) sera utilisé dans l'URL
# Le nom du modèle (valeur) est le nom de la classe du modèle Django
REPORT_MODEL_MAPPING = {
    'installs': 'google_play_installs_overview',
    'revenue': 'google_play_earnings',
    'subscriptions': 'google_play_subscriptions_overview',
    'reviews': 'google_play_reviews',
    'sales': 'google_play_sales',
    'crashes': 'google_play_crashes_overview',
    'ratings': 'google_play_ratings_overview',
    # Ajoutez d'autres rapports ici au besoin
}

def get_model_for_report(report_type):
    """Récupère la classe du modèle Django pour un type de rapport donné."""
    model_name = REPORT_MODEL_MAPPING.get(report_type)
    if not model_name:
        return None
    try:
        # 'play_reports' est le nom de votre application Django
        return apps.get_model('play_reports', model_name)
    except LookupError:
        return None

def create_dynamic_serializer(model_class):
    """Crée une classe de sérialiseur ModelSerializer à la volée pour un modèle donné."""
    class DynamicSerializer(serializers.ModelSerializer):
        class Meta:
            model = model_class
            fields = '__all__'
    return DynamicSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def list_report_types(request):
    """Renvoie la liste des types de rapports disponibles."""
    return Response(list(REPORT_MODEL_MAPPING.keys()))

@api_view(['GET'])
@permission_classes([AllowAny])
def get_report_data(request, report_type):
    """API view pour renvoyer les données d'un rapport en fonction de son type."""
    model_class = get_model_for_report(report_type)

    if model_class is None:
        return Response(
            {'error': f'Invalid report type: {report_type}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    queryset = model_class.objects.all()
    DynamicSerializer = create_dynamic_serializer(model_class)
    serializer = DynamicSerializer(queryset, many=True)

    return Response(serializer.data)
