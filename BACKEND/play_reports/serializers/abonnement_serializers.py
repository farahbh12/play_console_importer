# serializers/abonnement_serializers.py
from rest_framework import serializers
from play_reports.models import Abonnement, Client, TypeAbonnement
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError

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
    nom = serializers.SerializerMethodField()
    prenom = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    date_creation = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    
    class Meta:
        model = Abonnement
        fields = [
            'id_abonnement',
            'type_abonnement',
            'is_active',
            'date_creation',
            'prenom',
            'nom',
            'email'
        ]
        read_only_fields = fields

    def get_nom(self, obj):
        client = obj.clients.first()
        return client.last_name if client else ''

    def get_prenom(self, obj):
        client = obj.clients.first()
        return client.first_name if client else ''

    def get_email(self, obj):
        client = obj.clients.first()
        if client and hasattr(client, 'user') and client.user:
            return client.user.email
        return ''

class UpdateAbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abonnement
        fields = ['type_abonnement', 'is_active']
        extra_kwargs = {
            'type_abonnement': {'required': False},
            'is_active': {'required': False}
        }