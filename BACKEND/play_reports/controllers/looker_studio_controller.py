from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from play_reports.serializers.looker_studio_serializers import TableDataRequestSerializer
from .authentication import LookerStudioKeyAuthentication # Nouveau système d'authentification
from rest_framework.permissions import AllowAny # Permissions simplifiées
import logging
import datetime
import decimal

logger = logging.getLogger(__name__)

class TableListView(APIView):
    authentication_classes = [LookerStudioKeyAuthentication]
    permission_classes = [AllowAny] # La sécurité est maintenant gérée par la clé API statique
    
    # IMPORTANT: Remplissez cette liste avec les noms exacts de vos tables/vues en base de données
    ALLOWED_TABLES = [
        'google_play_installs_overview', 
    'google_play_installs_dimensioned',
    'google_play_subscriptions_overview',
    'google_play_subscriptions_dimensioned',
    'google_play_retained_installers_dimensioned',
    'google_play_retained_installers_overview',
    'google_play_crashes_overview',
    'google_play_crashes_dimensioned',
    'google_play_buyers_7d_overview',
    'google_play_buyers_7d_dimensioned',
    'google_play_earnings',
    'google_play_estimatedSales', 
    'google_play_subscription_cancellation_reasons',
    'google_play_store_performance_overview',
    'google_play_store_performance_dimensioned',
    'google_play_ratings_overview',
    'google_play_ratings_dimensioned',
    'google_play_reviews',
    'google_play_promotional_content',
   
    'google_play_buyers_7d_dimensioned',
      
    ]

    def get(self, request):
        """Liste des tables disponibles avec métadonnées pour le menu de configuration de Looker Studio."""
        return Response({
            'tables': [
                {
                    'name': table,
                    'label': self._format_table_name(table),
                    'type': 'overview' if 'overview' in table else 'dimensioned'
                }
                for table in self.ALLOWED_TABLES
            ]
        })
    
    def _format_table_name(self, table_name):
        """Formattage convivial des noms de tables pour l'affichage."""
        return table_name.replace('google_play_', '').replace('_', ' ').title()

class TableSchemaView(APIView):
    authentication_classes = [LookerStudioKeyAuthentication]
    permission_classes = [AllowAny] # La sécurité est maintenant gérée par la clé API statique
    
    def get(self, request, table_name):
        """Détection dynamique du schéma avec typage intelligent pour la fonction getSchema de Looker Studio."""
        if table_name not in TableListView.ALLOWED_TABLES:
            return Response({'error': 'Table non autorisée'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with connection.cursor() as cursor:
                # Utilise information_schema pour une détection fiable des colonnes et types
                cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, [table_name])
                
                schema = [self._map_column_type(col[0], col[1]) for col in cursor.fetchall()]
                return Response({'schema': schema})
        
        except Exception as e:
            logger.error(f"Erreur de schéma pour {table_name}: {str(e)}", exc_info=True)
            return Response({'error': f'Erreur serveur: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _map_column_type(self, name, data_type):
        """Mappage avancé des types PostgreSQL vers les types et sémantiques de Looker Studio."""
        type_mapping = {
            'integer': 'NUMBER',
            'bigint': 'NUMBER',
            'numeric': 'NUMBER',
            'double precision': 'NUMBER',
            'text': 'STRING',
            'character varying': 'STRING',
            'timestamp with time zone': 'DATETIME',
            'timestamp without time zone': 'DATETIME',
            'date': 'DATETIME',
            'boolean': 'BOOLEAN'
        }
        looker_type = type_mapping.get(data_type, 'STRING')
        
        # Détermine si un champ est une métrique ou une dimension
        is_metric = looker_type == 'NUMBER' and name not in ['year', 'month', 'day']

        return {
            'name': name,
            'label': name.replace('_', ' ').title(),
            'dataType': looker_type,
            'semantics': {
                'conceptType': 'METRIC' if is_metric else 'DIMENSION',
                'semanticType': self._detect_semantic_type(name, looker_type)
            }
        }
    
    def _detect_semantic_type(self, name, looker_type):
        """Détection du type sémantique pour une meilleure intégration (ex: devises, pourcentages)."""
        if looker_type == 'DATETIME':
            return 'YEAR_MONTH_DAY'
        if any(k in name for k in ['revenue', 'amount', 'price', 'krw']):
            return 'CURRENCY_KRW' # Adaptez le code devise si nécessaire
        if 'rate' in name or 'ratio' in name:
            return 'PERCENT'
        if 'country' in name:
            return 'COUNTRY'
        return None

class TableDataView(APIView):
    authentication_classes = [LookerStudioKeyAuthentication]
    permission_classes = [AllowAny] # La sécurité est maintenant gérée par la clé API statique

    def post(self, request, table_name):
        """Endpoint optimisé pour la fonction getData de Looker Studio."""
        serializer = TableDataRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if table_name not in TableListView.ALLOWED_TABLES:
            return Response({'error': 'Table non autorisée'}, status=status.HTTP_403_FORBIDDEN)

        try:
            schema_view = TableSchemaView()
            schema_response = schema_view.get(request, table_name)
            if schema_response.status_code != 200:
                return schema_response
            schema_map = {item['name']: item for item in schema_response.data['schema']}

            query, params = self._build_query(table_name, serializer.validated_data, schema_map)
            
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return self._format_response(cursor, schema_map)

        except Exception as e:
            logger.error(f"Erreur de données pour {table_name}: {str(e)}", exc_info=True)
            return Response({'error': f'Erreur serveur: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _build_query(self, table_name, validated_data, schema_map):
        """Construction sécurisée de la requête SQL avec filtres dynamiques."""
        fields = validated_data.get('fields', [])
        
        if not fields or fields == ['*']:
            select_clause = '*'
        else:
            valid_fields = [f for f in fields if f in schema_map]
            if not valid_fields:
                raise ValueError("Aucun des champs demandés n'est valide.")
            select_clause = '"' + '", "'.join(valid_fields) + '"'

        query = f'SELECT {select_clause} FROM "{table_name}"'

        where_clauses = []
        params = []

        date_range = validated_data.get('dateRange')
        date_column = validated_data.get('dateColumn')
        if date_range and date_column and date_column in schema_map:
            where_clauses.append(f'"{date_column}" BETWEEN %s AND %s')
            params.extend([date_range['startDate'], date_range['endDate']])

        filters = validated_data.get('filters', [])
        for f in filters:
            field_name = f.get('field')
            values = f.get('values')
            if field_name and field_name in schema_map and values:
                placeholders = ', '.join(['%s'] * len(values))
                where_clauses.append(f'"{field_name}" IN ({placeholders})')
                params.extend(values)

        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)

        limit = validated_data.get('limit', 10000)
        query += ' LIMIT %s'
        params.append(limit)

        return query, params

    def _format_response(self, cursor, schema_map):
        """Formatage des résultats (schéma et lignes) pour Looker Studio."""
        columns = [desc[0] for desc in cursor.description]
        response_schema = [schema_map[col] for col in columns if col in schema_map]

        rows = []
        for row in cursor.fetchall():
            formatted_row = []
            for value in row:
                if isinstance(value, (datetime.date, datetime.datetime)):
                    formatted_row.append(value.isoformat())
                elif isinstance(value, decimal.Decimal):
                    formatted_row.append(float(value))
                else:
                    formatted_row.append(value)
            rows.append({'values': formatted_row})

        return Response({
            'schema': response_schema,
            'rows': rows
        })

class TestAuthView(APIView):
    """
    Vue simple pour que le connecteur Looker Studio puisse tester le token API.
    Elle vérifie simplement que le token est valide.
    """
    authentication_classes = [LookerStudioKeyAuthentication]
    permission_classes = [AllowAny] # La sécurité est maintenant gérée par la clé API statique

    def get(self, request, *args, **kwargs):
        return Response({"detail": "Authentification réussie."}, status=status.HTTP_200_OK)