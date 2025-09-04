# serializers/abonnement_serializers.py
from rest_framework import serializers
from play_reports.models import Abonnement, Client, ClientStatus, TypeAbonnement
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class ClientAbonnementSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    nom = serializers.CharField(required=True, allow_blank=False)
    prenom = serializers.CharField(required=True, allow_blank=False)
    type_abonnement = serializers.ChoiceField(
        choices=TypeAbonnement.choices,
        required=True,
        allow_blank=False
    )

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("L'email est requis")
        return value.lower().strip()

    def validate_nom(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le nom est requis")
        return value.strip()

    def validate_prenom(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le prénom est requis")
        return value.strip()

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data.get('email')
        nom = validated_data.get('nom')
        prenom = validated_data.get('prenom')
        type_abonnement = validated_data.get('type_abonnement')
        
        try:
            # Vérifier si l'utilisateur existe déjà
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': prenom,
                    'last_name': nom,
                    'is_active': True
                }
            )
            
            # Mettre à jour les informations de l'utilisateur si nécessaire
            if not user_created:
                update_needed = False
                if user.first_name != prenom:
                    user.first_name = prenom
                    update_needed = True
                if user.last_name != nom:
                    user.last_name = nom
                    update_needed = True
                if update_needed:
                    user.save(update_fields=['first_name', 'last_name'])
            
            # Récupérer ou créer l'abonnement
            abonnement, _ = Abonnement.objects.get_or_create(
                type_abonnement=type_abonnement,
                defaults={
                    'is_active': True,
                    
                }
            )
            
            # Mettre à jour ou créer le client
            client, client_created = Client.objects.update_or_create(
                user=user,
                defaults={
                    'first_name': prenom,
                    'last_name': nom,
                    'abonnement': abonnement,
                    'is_active': True
                }
            )
            
            return {
                'success': True,
                'client_id': client.id,
                'email': user.email,
                'nom': user.last_name,
                'prenom': user.first_name,
                'abonnement_id': abonnement.id_abonnement,
                'abonnement_type': abonnement.get_type_abonnement_display(),
                'is_new_client': client_created,
                'is_new_user': user_created
            }
            
        except Exception as e:
            error_msg = f"Une erreur est survenue lors de la création de l'abonnement: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise serializers.ValidationError(error_msg)

class AbonnementClientSerializer(serializers.ModelSerializer):
    type_abonnement_display = serializers.SerializerMethodField()
    clients_info = serializers.SerializerMethodField()
    client_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Abonnement
        fields = [
            'id_abonnement', 
            'type_abonnement', 
            'type_abonnement_display',
            'is_active',
            'date_creation',
            'date_mise_a_jour',
            'clients_info',
            'client_count'
        ]
        read_only_fields = fields
    
    def get_type_abonnement_display(self, obj):
        return obj.get_type_abonnement_display()

    def get_clients_info(self, obj):
        clients = getattr(obj, 'owner_clients', None) or obj.clients.filter(
            role_client='Owner',
            status=ClientStatus.ACTIVE
        ).select_related('user')
        
        client_list = []
        for client in clients:
            user = getattr(client, 'user', None)
            
            client_data = {
                'id': client.id,
                'user_id': user.id if user else None,
                'first_name': user.first_name if user and user.first_name else client.first_name or '',
                'last_name': user.last_name if user and user.last_name else client.last_name or 'Non spécifié',
                'email': user.email if user and user.email else client.email or 'Email non disponible',
                'role': client.role_client,
                'status': client.status,
                'abonnement': {
                    'id': obj.id_abonnement,
                    'type': obj.type_abonnement,
                    'type_display': obj.get_type_abonnement_display(),
                    'is_active': obj.is_active,
                    'date_creation': obj.date_creation.isoformat() if hasattr(obj, 'date_creation') and obj.date_creation else None,
                    'date_mise_a_jour': obj.date_mise_a_jour.isoformat() if hasattr(obj, 'date_mise_a_jour') and obj.date_mise_a_jour else None
                },
                'tenant_id': client.tenant_id or None,
                'created_at': client.created_at.isoformat() if hasattr(client, 'created_at') and client.created_at else None,
                'updated_at': client.updated_at.isoformat() if hasattr(client, 'updated_at') and client.updated_at else None
            }
            
            # Ajouter date_fin uniquement si elle existe dans le modèle
            if hasattr(obj, 'date_fin'):
                client_data['abonnement']['date_fin'] = obj.date_fin.isoformat() if obj.date_fin else None
                
            client_list.append(client_data)
            
        return client_list

class AbonnementSerializer(serializers.ModelSerializer):
    """
    Serializer for the Abonnement model.
    Used for displaying subscription details in the API.
    """
    class Meta:
        model = Abonnement
        fields = [
            'id_abonnement',
            'type_abonnement',
            'is_active',
            'date_creation',
            'date_mise_a_jour'
        ]
        read_only_fields = ['id_abonnement', 'date_creation']

class UpdateAbonnementSerializer(serializers.ModelSerializer):
    id_abonnement = serializers.IntegerField(required=True)
    type_abonnement = serializers.CharField(
        required=False,
        allow_blank=False,
        error_messages={
            'blank': 'Le type d\'abonnement ne peut pas être vide.'
        }
    )
    
    class Meta:
        model = Abonnement
        fields = ['id_abonnement', 'type_abonnement', 'is_active']
        read_only_fields = ['id_abonnement']
        extra_kwargs = {
            'is_active': {'required': False}
        }
    
    def validate_type_abonnement(self, value):
        if not value:
            return value
            
        # Convertir en majuscules pour la validation
        value = value.upper().strip()
        
        # Vérifier que la valeur est dans les choix valides (insensible à la casse)
        valid_choices = dict(TypeAbonnement.choices)
        valid_choices_upper = {k.upper(): k for k in valid_choices}
        
        if value not in valid_choices_upper:
            raise serializers.ValidationError(
                f"Type d'abonnement invalide. Les choix valides sont: {', '.join(valid_choices.values())}"
            )
        
        # Retourner la valeur avec la casse exacte du modèle
        return valid_choices_upper[value]