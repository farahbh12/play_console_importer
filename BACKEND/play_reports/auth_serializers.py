from rest_framework import serializers
from django.contrib.auth import get_user_model
from play_reports.models.employee import Employee, RoleEmploye
from play_reports.models.client import Client, RoleClient

User = get_user_model()

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'email', 'first_name', 'last_name', 'role_employe', 'date_joined']
        extra_kwargs = {'date_joined': {'read_only': True}}

class EmployeeRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    role_employe = serializers.ChoiceField(choices=RoleEmploye.choices, required=True)

    def validate(self, data):
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        return data

class ClientSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'user_id', 'email', 'first_name', 'last_name', 'role_client',
            'is_active', 'tenant', 'created_at', 'updated_at', 'abonnement_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'abonnement_id']
        extra_kwargs = {
            'tenant': {'required': False, 'allow_null': True}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['first_name'] = instance.first_name
        representation['last_name'] = instance.last_name
        return representation

class ClientRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    def validate(self, data):
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        return data

class EmployeeLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, trim_whitespace=False)

class ClientLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

class EmployeeTokenObtainPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField()

class ClientTokenObtainPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField()

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, write_only=True)
