from rest_framework import serializers
from datetime import datetime

class TableDataRequestSerializer(serializers.Serializer):
    """
    Valide la structure des requêtes de données envoyées par Looker Studio.
    Ceci correspond à l'objet `request` reçu par la fonction `getData` dans Apps Script.
    """
    fields = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=[]
    )
    dateRange = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        allow_null=True
    )
    dateColumn = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=True
    )
    filters = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=[]
    )
    limit = serializers.IntegerField(
        min_value=1,
        max_value=50000,
        required=False,
        default=10000
    )
    
    def validate_dateRange(self, value):
        """Valide que la plage de dates contient startDate et endDate au format YYYY-MM-DD."""
        if not value or not value.get('startDate') or not value.get('endDate'):
            # Permet les requêtes sans plage de dates
            return value
            
        try:
            # Looker Studio envoie les dates au format YYYY-MM-DD
            datetime.strptime(value['startDate'], '%Y-%m-%d')
            datetime.strptime(value['endDate'], '%Y-%m-%d')
        except (ValueError, TypeError):
            raise serializers.ValidationError("Le format des dates dans dateRange doit être 'YYYY-MM-DD'.")
            
        return value
    
    def validate_filters(self, value):
        """Valide que chaque filtre a un champ et des valeurs."""
        for f in value:
            if 'field' not in f or 'values' not in f:
                raise serializers.ValidationError("Chaque filtre doit contenir les clés 'field' et 'values'.")
            if not isinstance(f['values'], list):
                raise serializers.ValidationError("La clé 'values' d'un filtre doit être une liste.")
        return value
