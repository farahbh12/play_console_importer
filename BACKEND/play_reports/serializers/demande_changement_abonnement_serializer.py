from rest_framework import serializers
from play_reports.models import DemandeChangementAbonnement

class DemandeChangementAbonnementSerializer(serializers.ModelSerializer):
    """
    Serializer pour les demandes de changement d'abonnement
    """
    ancien_abonnement_nom = serializers.CharField(source='ancien_abonnement.type_abonnement', read_only=True)
    nouvel_abonnement_nom = serializers.CharField(source='nouvel_abonnement.type_abonnement', read_only=True)
    client_nom = serializers.CharField(source='client.user.get_full_name', read_only=True)
    client_email = serializers.EmailField(source='client.user.email', read_only=True)
    
    class Meta:
        model = DemandeChangementAbonnement
        fields = [
            'id',
            'client',
            'client_nom',
            'client_email',
            'ancien_abonnement',
            'ancien_abonnement_nom',
            'nouvel_abonnement',
            'nouvel_abonnement_nom',
            'message',
            'statut',
            'date_demande',
            'date_traitement',
            'traite_par',
            'commentaire_traitement'
        ]
        read_only_fields = [
            'id', 'client', 'ancien_abonnement', 'statut', 
            'date_demande', 'date_traitement', 'traite_par',
            'commentaire_traitement'
        ]

class CreateDemandeChangementAbonnementSerializer(serializers.Serializer):
    """
    Serializer pour la création d'une demande de changement d'abonnement
    """
    plan_id = serializers.IntegerField(required=True)
    message = serializers.CharField(required=False, allow_blank=True)
    
    def validate_plan_id(self, value):
        from play_reports.models import Abonnement
        try:
            Abonnement.objects.get(id=value, is_active=True)
        except Abonnement.DoesNotExist:
            raise serializers.ValidationError("Le forfait demandé n'existe pas ou n'est pas actif")
        return value
    
    def create(self, validated_data):
        pass  # La création est gérée dans la vue
        
    def update(self, instance, validated_data):
        pass  # Non utilisé pour la création
