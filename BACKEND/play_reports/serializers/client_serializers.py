from rest_framework import serializers
from play_reports.models import Abonnement, Client, TypeAbonnement
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']

class ClientSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='get_role_client_display', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    abonnement_type = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'user_id', 'first_name', 'last_name', 'email', 
            'role', 'is_active', 'abonnement_type'
        ]

    def get_abonnement_type(self, obj):
        if hasattr(obj, 'abonnement') and obj.abonnement:
            return obj.abonnement.get_type_abonnement_display()
        return 'Aucun'

class ClientDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    # Utiliser les champs de la table Client, pas User
    role = serializers.CharField(source='get_role_client_display', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    abonnement = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'user', 'email', 'first_name', 'last_name', 'role', 
            'date_joined', 'last_login', 'is_active', 'abonnement', 'created_at', 'updated_at'
        ]

    def get_abonnement(self, obj):
        if hasattr(obj, 'abonnement') and obj.abonnement:
            return {
                'id': obj.abonnement.id_abonnement,
                'type': obj.abonnement.get_type_abonnement_display(),
                'is_active': obj.abonnement.is_active,
                'date_creation': obj.abonnement.date_creation,
                'date_mise_a_jour': obj.abonnement.date_mise_a_jour
            }
        return None

class ClientUpdateSerializer(serializers.ModelSerializer):
    # Les champs first_name et last_name sont dans la table Client
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'email', 'password']

    def update(self, instance, validated_data):
        user = instance.user
        
        # Update Client fields (first_name, last_name sont dans Client)
        if 'first_name' in validated_data:
            instance.first_name = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            instance.last_name = validated_data.pop('last_name')
        
        # Update User fields (email, password sont dans User)
        if 'email' in validated_data:
            user.email = validated_data.pop('email')
        
        password = validated_data.pop('password', None)
        if password:
            user.set_password(password)
        
        user.save()
        instance.save()
        
        return instance