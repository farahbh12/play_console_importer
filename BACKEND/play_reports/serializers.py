from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from play_reports.models.employee import Employee, RoleEmploye
from play_reports.models.client import Client,RoleClient
from play_reports.models.tenant import Tenant
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model





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
    role_employe = serializers.ChoiceField(
        choices=RoleEmploye.choices,
        required=True  # Obligatoire, sans valeur par défaut
    )

    def validate(self, data):
        # Vérifie que les mots de passe correspondent
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({
                "password_confirm": "Les mots de passe ne correspondent pas."
            })

        # Vérifie l'unicité de l'email
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({
                "email": "Un utilisateur avec cet email existe déjà."
            })

        # Vérifie que role_employe est présent (normalement fait par DRF, mais on double au cas où)
        if 'role_employe' not in data:
            raise serializers.ValidationError({
                "role_employe": "Ce champ est obligatoire."
            })

        # Vérifie qu’il n’existe pas déjà un administrateur si on veut en créer un autre
        if data['role_employe'] == RoleEmploye.ADMINISTRATEUR:
            if Employee.objects.filter(role_employe=RoleEmploye.ADMINISTRATEUR).exists():
                raise serializers.ValidationError({
                    "role_employe": "Un administrateur existe déjà dans le système."
                })

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)

        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        role_employe = validated_data.pop('role_employe')

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )

        employee = Employee.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            role_employe=role_employe
        )

        return employee


class EmployeeTokenObtainPairSerializer(serializers.Serializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = 'employee'
        return token

class ClientSerializer(serializers.ModelSerializer):
    # Déclarer les champs supplémentaires qui viennent du modèle User lié
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Client
        # Assurer que user_id et is_active sont bien dans la liste des champs
        fields = [
            'id', 'user_id', 'email', 'first_name', 'last_name', 'role_client',
            'is_active', 'tenant', 'created_at', 'updated_at', 'abonnement_id'
        ]
        # Les champs read_only sont déjà gérés par leur déclaration explicite ci-dessus
        read_only_fields = ['id', 'created_at', 'updated_at', 'abonnement_id']
        extra_kwargs = {
            'tenant': {'required': False, 'allow_null': True}
        }

    def to_representation(self, instance):
        """S'assure que les champs first_name et last_name viennent bien du modèle Client."""
        representation = super().to_representation(instance)
        representation['first_name'] = instance.first_name
        representation['last_name'] = instance.last_name
        return representation

class ClientRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(
        required=True, 
        max_length=150, 
        allow_blank=False
    )
    last_name = serializers.CharField(
        required=True, 
        max_length=150, 
        allow_blank=False
    )

    class Meta:
        fields = [
            'email', 'password', 'password_confirm', 
            'first_name', 'last_name'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data.get('password_confirm'):
            raise serializers.ValidationError({
                "password_confirm": "Les mots de passe ne correspondent pas."
            })
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                "email": "Un utilisateur avec cet email existe déjà."
            })
            
        return data

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        validated_data.pop('password_confirm', None)
        
        # Créer l'utilisateur (sans first_name et last_name)
        user = User.objects.create_user(
            email=email,
            password=password,
            is_active=True
        )
        
        # Créer le client avec first_name et last_name
        client = Client.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            role_client=RoleClient.OWNER,
            tenant=None
        )
        
        return client
class EmployeeLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email', '').strip()
        password = attrs.get('password', '')

        if not email or not password:
            raise serializers.ValidationError({
                "non_field_errors": ["L'email et le mot de passe sont obligatoires."]
            })

        try:
            # Vérifier d'abord si l'utilisateur existe
            user = User.objects.filter(email=email).first()
            if not user:
                raise serializers.ValidationError({
                    "email": ["Aucun compte trouvé avec cet email."]
                })

            # Vérifier si l'utilisateur est un employé
            try:
                employee = Employee.objects.get(user=user)
            except Employee.DoesNotExist:
                raise serializers.ValidationError({
                    "non_field_errors": ["Aucun compte employé trouvé avec cet email."]
                })

            # Vérifier le mot de passe
            if not user.check_password(password):
                raise serializers.ValidationError({
                    "password": ["Mot de passe incorrect."]
                })

            # Vérifier si le compte est actif
            if not user.is_active:
                raise serializers.ValidationError({
                    "non_field_errors": ["Ce compte est désactivé."]
                })

            attrs['user'] = user
            attrs['employee'] = employee
            return attrs
            
        except Exception as e:
            # En cas d'erreur inattendue, logger et renvoyer une erreur générique
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la validation de la connexion: {str(e)}")
            raise serializers.ValidationError({
                "non_field_errors": ["Une erreur est survenue lors de la connexion."]
            })

class ClientLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Veuillez fournir un email et un mot de passe.")

        try:
            client = Client.objects.get(user__email=email)
            user = client.user
        except Client.DoesNotExist:
            raise serializers.ValidationError({"email": "Aucun client trouvé avec cet email."})

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Mot de passe incorrect."})

        if not user.is_active:
            raise serializers.ValidationError("Ce compte est désactivé.")

        attrs['user'] = user
        attrs['client'] = client
        return attrs

    def create(self, validated_data):
        # Cette méthode est requise mais ne sera pas utilisée
        pass

    def update(self, instance, validated_data):
        # Cette méthode est requise mais ne sera pas utilisée
        pass



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

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Aucun utilisateur avec cet e-mail.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data['uidb64']))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError("Lien invalide.")
        if not PasswordResetTokenGenerator().check_token(user, data['token']):
            raise serializers.ValidationError("Token invalide ou expiré.")
        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
