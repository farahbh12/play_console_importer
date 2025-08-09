from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from ..services import report_service
from ..serializers.report_serializer import create_dynamic_serializer

@api_view(['GET'])
@permission_classes([AllowAny])
def list_report_types(request):
    """Renvoie la liste des types de rapports disponibles via le service."""
    report_types = report_service.list_available_reports()
    return Response(report_types)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_report_data(request, report_type):
    """API view pour renvoyer les données d'un rapport en fonction de son type."""
    model_class = report_service.get_model_for_report(report_type)

    if model_class is None:
        return Response(
            {'error': f'Invalid report type: {report_type}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    queryset = report_service.get_report_queryset(report_type)
    DynamicSerializer = create_dynamic_serializer(model_class)
    serializer = DynamicSerializer(queryset, many=True)

    return Response(serializer.data)
