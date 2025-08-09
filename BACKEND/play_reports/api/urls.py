from django.urls import path
from .views import get_report_data, list_report_types

urlpatterns = [
    path('reports/types/', list_report_types, name='list_report_types'),
    path('reports/<str:report_type>/', get_report_data, name='get_report_data'),
]
