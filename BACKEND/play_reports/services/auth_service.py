from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError

from play_reports.models.employee import Employee, RoleEmploye
from play_reports.models.client import Client, RoleClient
from play_reports.models.tenant import Tenant

User = get_user_model()

class AuthService:

    @staticmethod
    def register_employee(validated_data):
        if User.objects.filter(email=validated_data['email']).exists():
            raise ValidationError({"email": "Un utilisateur avec cet email existe déjà."})
        
        if validated_data['role_employe'] == RoleEmploye.ADMINISTRATEUR and Employee.objects.filter(role_employe=RoleEmploye.ADMINISTRATEUR).exists():
            raise ValidationError({"role_employe": "Un administrateur existe déjà dans le système."})

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=True
        )

        employee = Employee.objects.create(
            user=user,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role_employe=validated_data['role_employe']
        )
        return employee

    @staticmethod
    def register_client(validated_data):
        if User.objects.filter(email=validated_data['email']).exists():
            raise ValidationError({"email": "Un utilisateur avec cet email existe déjà."})

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=True
        )

        client = Client.objects.create(
            user=user,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role_client=RoleClient.OWNER,  # Default role
        )
        return client

    @staticmethod
    def login_employee(email, password):
        try:
            employee = Employee.objects.get(user__email=email)
            user = employee.user
        except Employee.DoesNotExist:
            # Vérifier si l'email correspond à un compte client -> mismatch de type
            try:
                Client.objects.get(user__email=email)
                raise ValidationError({
                    "code": "ROLE_MISMATCH",
                    "detail": "Ce compte n'appartient pas à l'espace Employé. Sélectionnez 'Client'."
                })
            except Client.DoesNotExist:
                raise ValidationError({
                    "code": "invalid_account",
                    "detail": "Aucun compte employé trouvé avec cet email."
                })

        if not user.check_password(password):
            raise ValidationError({
                "code": "invalid_credentials",
                "detail": "Mot de passe incorrect."
            })

        if not user.is_active:
            raise ValidationError({
                "code": "inactive_account",
                "detail": "Ce compte est désactivé."
            })

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': 'employee',
                'role': employee.role_employe,
                'is_superuser': user.is_superuser,
            }
        }

    @staticmethod
    def login_client(email, password):
        try:
            client = Client.objects.get(user__email=email)
            user = client.user
        except Client.DoesNotExist:
            # Vérifier si l'email correspond à un compte employé -> mismatch de type
            try:
                Employee.objects.get(user__email=email)
                raise ValidationError({
                    "code": "ROLE_MISMATCH",
                    "detail": "Ce compte n'appartient pas à l'espace Client. Sélectionnez 'Employé'."
                })
            except Employee.DoesNotExist:
                raise ValidationError({
                    "code": "invalid_account",
                    "detail": "Aucun client trouvé avec cet email."
                })

        if not user.check_password(password):
            raise ValidationError({
                "code": "invalid_credentials",
                "detail": "Mot de passe incorrect."
            })

        if not user.is_active:
            raise ValidationError({
                "code": "inactive_account",
                "detail": "Ce compte est désactivé."
            })

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        refresh = RefreshToken.for_user(user)
        # Vérifier si le client a un tenant et une URI GCS valide
        requires_gcs_validation = not (client.tenant and hasattr(client.tenant, 'gcs_uri') and client.tenant.gcs_uri)
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': client.id,
                'email': user.email,
                'user_type': 'client',
                'role': client.role_client,
                'is_active': user.is_active,
                'last_login': user.last_login,
                'tenant_id': client.tenant.id if client.tenant else None,
                'requires_gcs_validation': requires_gcs_validation
            }
        }

    @staticmethod
    def send_password_reset_email(email):
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            reset_link = f"{settings.FRONTEND_URL}/reset-password-confirm/?uid={uid}&token={token}"

            send_mail(
                subject="Réinitialisation de votre mot de passe",
                message=f"Bonjour,\n\nVoici le lien pour réinitialiser votre mot de passe : {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )
        except User.DoesNotExist:
            # Do not reveal if the user does not exist
            pass

    @staticmethod
    def confirm_password_reset(uidb64, token, new_password):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            raise ValidationError("Lien invalide.")

        if not PasswordResetTokenGenerator().check_token(user, token):
            raise ValidationError("Token invalide ou expiré.")

        user.set_password(new_password)
        user.save()
        return user
