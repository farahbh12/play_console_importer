from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class LookerConnectorView(APIView):
    permission_classes = [IsAuthenticated]

    def get_available_data_sources(self, subscription_plan='basic'):
        """Retourne les sources de données disponibles selon le plan d'abonnement"""
        basic_sources = [
            {
                'table': 'google_play_installs_overview',
                'display_name': 'Google Play - Installations',
                'description': 'Données d\'installation et désinstallation',
                'category': 'google_play'
            },
            {
                'table': 'google_play_ratings_overview',
                'display_name': 'Google Play - Évaluations',
                'description': 'Notes et évaluations des applications',
                'category': 'google_play'
            },
            {
                'table': 'google_play_reviews',
                'display_name': 'Google Play - Avis',
                'description': 'Avis détaillés des utilisateurs',
                'category': 'google_play'
            },
            {
                'table': 'google_play_crashes_overview',
                'display_name': 'Google Play - Crashes',
                'description': 'Rapports de crash des applications',
                'category': 'google_play'
            }
        ]

        premium_sources = [
            # Premium-only tables peuvent être ajoutées ici plus tard
        ]

        if subscription_plan in ['premium', 'enterprise']:
            return basic_sources + premium_sources
        return basic_sources

    def format_date_for_looker(self, date_value):
        """Formate les dates pour Looker Studio (YYYY-MM-DD ou YYYY-MM-DDTHH:mm:ss)"""
        if date_value is None:
            return None
        if isinstance(date_value, str):
            return date_value
        elif isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%dT%H:%M:%S')
        elif isinstance(date_value, date):
            return date_value.strftime('%Y-%m-%d')
        else:
            return str(date_value)

    def clean_row_for_looker(self, row_dict):
        """Nettoie une ligne de données pour Looker Studio"""
        internal_fields = ['id', 'tenant_id', 'created_at', 'updated_at', 'user_id']
        cleaned_row = {}
        for key, value in row_dict.items():
            if key in internal_fields:
                continue
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, (date, datetime)):
                        cleaned_row[nested_key] = self.format_date_for_looker(nested_value)
                    else:
                        cleaned_row[nested_key] = nested_value
            elif isinstance(value, list):
                cleaned_row[key] = ', '.join(str(item) for item in value)
            elif isinstance(value, (date, datetime)):
                cleaned_row[key] = self.format_date_for_looker(value)
            else:
                cleaned_row[key] = value
        return cleaned_row

    def generate_looker_schema(self, sample_rows):
        """Génère un schéma Looker Studio basé sur les données"""
        if not sample_rows:
            return []

        first_row = sample_rows[0]
        schema = []

        for field_name, value in first_row.items():
            if isinstance(value, bool):
                data_type = 'BOOLEAN'
                concept_type = 'DIMENSION'
            elif isinstance(value, (int, float)):
                data_type = 'NUMBER'
                concept_type = 'METRIC'
            elif isinstance(value, str):
                if value and (len(value) == 10 and value.count('-') == 2 or 'T' in value and ':' in value):
                    data_type = 'STRING'
                else:
                    data_type = 'STRING'
                concept_type = 'DIMENSION'
            else:
                data_type = 'STRING'
                concept_type = 'DIMENSION'

            schema_field = {
                'name': field_name,
                'dataType': data_type,
                'semantics': {
                    'conceptType': concept_type
                }
            }
            schema.append(schema_field)

        return schema

    def _create_field_schema(self, name, data_type, concept_type, semantic_type=None, is_reaggregatable=False):
        """Helper pour créer un schéma de champ standardisé"""
        schema = {
            'name': name,
            'dataType': data_type,
            'semantics': {
                'conceptType': concept_type
            }
        }
        if semantic_type:
            schema['semantics']['semanticType'] = semantic_type
        if is_reaggregatable:
            schema['semantics']['isReaggregatable'] = True
        return schema

    def get(self, request, table_name=None):
        """Gère les requêtes GET pour les métadonnées"""
        try:
            if not table_name:
                subscription_plan = getattr(request.user, 'subscription_plan', 'basic')
                available_sources = self.get_available_data_sources(subscription_plan)
                return Response({'success': True, 'data': {'sources': available_sources}})

            return Response({
                'success': True,
                'data': {
                    'table': table_name,
                    'message': 'Utilisez POST pour récupérer les données et le schéma'
                }
            })

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métadonnées: {str(e)}")
            return Response({'error': 'Erreur serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, table_name):
        """
        Méthode POST qui retourne les données dans le format attendu par Looker Studio
        """
        try:
            subscription_plan = getattr(request.user, 'subscription_plan', 'basic')
            available_sources = self.get_available_data_sources(subscription_plan)
            source_info = next((src for src in available_sources if src['table'] == table_name), None)

            if not source_info:
                return Response({'error': 'Accès non autorisé à cette source de données'}, status=status.HTTP_403_FORBIDDEN)

            query_params = request.data.get('query_params', {})
            limit = min(int(query_params.get('limit', 1000)), 10000)
            offset = int(query_params.get('offset', 0))
            start_date = query_params.get('start_date')
            end_date = query_params.get('end_date') or start_date
            package_name = query_params.get('package_name')
            date_field = query_params.get('date_field', 'date')

            # Configuration des tables
            tables_config = {
                'google_play_crashes_overview': {
                    'fields': ['date', 'package_name', 'device', 'daily_crashes', 'daily_anrs'],
                    'schema': [
                        self._create_field_schema('date', 'STRING', 'DIMENSION', 'YEAR_MONTH_DAY'),
                        self._create_field_schema('package_name', 'STRING', 'DIMENSION'),
                        self._create_field_schema('device', 'STRING', 'DIMENSION'),
                        self._create_field_schema('daily_crashes', 'NUMBER', 'METRIC', None, True),
                        self._create_field_schema('daily_anrs', 'NUMBER', 'METRIC', None, True)
                    ]
                },
                'google_play_installs_overview': {
                    'fields': [
                        'date', 'package_name', 'country', 'language', 'carrier',
                         'installs_on_active_devices',
                        'daily_device_installs', 'daily_user_installs', 'daily_user_uninstalls'
                    ],
                    'schema': [
                        self._create_field_schema('date', 'STRING', 'DIMENSION', 'YEAR_MONTH_DAY'),
                        self._create_field_schema('package_name', 'STRING', 'DIMENSION'),
                        self._create_field_schema('country', 'STRING', 'DIMENSION'),
                        self._create_field_schema('language', 'STRING', 'DIMENSION'),
                        self._create_field_schema('carrier', 'STRING', 'DIMENSION'),
                        self._create_field_schema('installs_on_active_devices', 'NUMBER', 'METRIC', None, True),
                        self._create_field_schema('daily_device_installs', 'NUMBER', 'METRIC', None, True),
                        self._create_field_schema('daily_user_installs', 'NUMBER', 'METRIC', None, True),
                        self._create_field_schema('daily_user_uninstalls', 'NUMBER', 'METRIC', None, True)
                    ]
                },
                'google_play_ratings_overview': {
                    'fields': ['date', 'package_name', 'daily_average_rating', 'total_average_rating'],
                    'schema': [
                        self._create_field_schema('date', 'STRING', 'DIMENSION', 'YEAR_MONTH_DAY'),
                        self._create_field_schema('package_name', 'STRING', 'DIMENSION'),
                        self._create_field_schema('daily_average_rating', 'NUMBER', 'METRIC', None, True),
                        self._create_field_schema('total_average_rating', 'NUMBER', 'METRIC', None, True)
                    ]
                }
            }

            table_config = tables_config.get(table_name, {'fields': ['*'], 'schema': []})
            fields = table_config['fields']

            # Construction de la requête SQL
            select_fields = ', '.join(fields) if fields != ['*'] else '*'
            query = f"SELECT {select_fields} FROM {table_name} WHERE 1=1"
            params = []

            if start_date:
                query += f" AND {date_field} >= %s"
                params.append(start_date)
            if end_date and end_date != start_date:
                query += f" AND {date_field} <= %s"
                params.append(end_date)
            if package_name:
                query += " AND package_name = %s"
                params.append(package_name)

            query += f" ORDER BY {date_field} DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Exécution de la requête
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

                result_rows = []
                for row in rows:
                    row_data = dict(zip(columns, row))
                    if fields != ['*']:
                        row_data = {k: v for k, v in row_data.items() if k in fields}
                    result_rows.append(row_data)

            return Response({'schema': table_config['schema'], 'rows': result_rows})

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données: {str(e)}", exc_info=True)
            return Response({'error': f'Erreur lors de la récupération des données: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DebugTableStructureView(APIView):
    """Vue pour déboguer la structure des tables"""
    permission_classes = [IsAuthenticated]

    def get(self, request, table_name):
        """Retourne la structure et un échantillon de données de la table spécifiée"""
        try:
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, [table_name])
                    columns = [{'name': col[0], 'type': col[1]} for col in cursor.fetchall()]

                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    sample_data = [
                        dict(zip([col[0] for col in cursor.description], row))
                        for row in cursor.fetchall()
                    ]

                    return Response({
                        'success': True,
                        'table': table_name,
                        'columns': columns,
                        'sample_data': sample_data
                    })
                else:
                    return Response({
                        'error': 'Base de données non supportée pour le débogage',
                        'vendor': connection.vendor
                    }, status=400)
        except Exception as e:
            return Response({'error': str(e), 'table': table_name}, status=500)
