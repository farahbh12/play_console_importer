from rest_framework import serializers
from django.contrib.auth import get_user_model
from play_reports.models import Employee

User = get_user_model()

class EmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    role_employe = serializers.CharField(source='get_role_employe_display', read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'first_name', 'last_name', 'email', 'role_employe']
        read_only_fields = ['id']
        

class EmployeeDetailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    role_employe = serializers.CharField(source='get_role_employe_display', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'email', 
            'role_employe', 'date_joined', 'last_login', 'is_active'
        ]

class EmployeeUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    is_active = serializers.BooleanField(source='user.is_active', required=False)

    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 'is_active']
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        # Mise à jour des champs utilisateur
        user = instance.user
        for attr, value in user_data.items():
            if value is not None:
                setattr(user, attr, value)
        user.save()
        
        # Mise à jour des champs employé
        instance = super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'email': instance.user.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'role': instance.get_role_employe_display() if hasattr(instance, 'get_role_employe_display') else None
        }