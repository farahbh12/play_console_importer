from django.conf import settings
import os
from django.db import models
from play_reports.models.abonnement import Abonnement, TypeAbonnement
from play_reports.models.invitation import Invitation, InvitationStatus
import uuid
from datetime import timedelta
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

class RoleClient(models.TextChoices):
    OWNER = 'Owner', 'Owner'
    MEMBRE_INVITE = 'MEMBRE_INVITE', 'Membre Invité'

class ClientStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Actif'
    INVITED = 'INVITED', 'Invité'
    INACTIVE = 'INACTIVE', 'Inactif'

class Client(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_profile',
        null=True, blank=True
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    role_client = models.CharField(max_length=20, choices=RoleClient.choices, default=RoleClient.OWNER)
    status = models.CharField(max_length=20, choices=ClientStatus.choices, default=ClientStatus.ACTIVE)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='invited_clients')
    tenant = models.ForeignKey(
        'play_reports.Tenant',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    abonnement = models.ForeignKey(
        Abonnement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='clients'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'play_reports_client'
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tenant'],
                name='unique_user_tenant',
                condition=~models.Q(tenant=None)
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.first_name} {self.last_name} ({self.get_role_client_display()})"
        
    def request_subscription_change(self, new_subscription_type):
        """
        Envoie une demande de changement d'abonnement à l'administrateur.
        Retourne un tuple (succès, message)
        """
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        # Vérifier si le type d'abonnement est valide
        valid_types = dict(TypeAbonnement.choices)
        if new_subscription_type not in valid_types:
            return False, "Type d'abonnement invalide."
            
        # Récupérer les informations du client
        client_info = f"""
        Client: {self.user.get_full_name()}
        Email: {self.user.email}
        Abonnement actuel: {self.abonnement.get_type_abonnement_display() if self.abonnement else 'Aucun'}
        Nouvel abonnement demandé: {valid_types[new_subscription_type]}
        """
        
        # Récupérer l'email de l'administrateur
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@example.com')
        
        # Sujet de l'email
        subject = f"Demande de changement d'abonnement - {self.user.email}"
        
        # Corps de l'email
        message = f"""
        Bonjour,
        
        Un client souhaite changer d'abonnement :
        
        {client_info}
        
        Cordialement,
        L'équipe Play Reports
        """
        
        try:
            # Envoyer l'email à l'administrateur
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=False,
            )
            return True, "Votre demande de changement d'abonnement a été envoyée avec succès. Nous vous contacterons bientôt."
            
        except Exception as e:
            print(f"Erreur lors de l'envoi de la demande de changement d'abonnement : {str(e)}")
            return False, "Une erreur est survenue lors de l'envoi de votre demande. Veuillez réessayer plus tard."

    @property
    def is_owner(self):
        return self.role_client == RoleClient.OWNER

    @property
    def is_member(self):
        return self.role_client == RoleClient.MEMBRE_INVITE
        
    def has_permission(self, permission_slug):
        """
        Vérifie si le client a une permission spécifique.
        """
        from django.contrib.auth.models import Permission as AuthPermission
        from django.contrib.contenttypes.models import ContentType
        
        # Les propriétaires ont toutes les permissions
        if self.role_client == RoleClient.OWNER:
            return True
            
        # Vérifier les permissions personnalisées
        try:
            # Vérifier les permissions personnalisées
            content_type = ContentType.objects.get_for_model(self)
            permission = AuthPermission.objects.get(
                content_type=content_type,
                codename=permission_slug
            )
            return self.user.user_permissions.filter(pk=permission.pk).exists()
        except AuthPermission.DoesNotExist:
            return False
    
    def can_invite_guest(self):
        """
        Vérifie si le client (Owner) peut inviter un nouveau membre.
        Retourne un tuple (bool, str): (peut_inviter, message_erreur)
        """
        if not self.is_owner:
            return False, "Seul le propriétaire du compte peut inviter des membres."

        if not self.abonnement:
            return False, "Aucun abonnement actif."

        if self.abonnement.type_abonnement == TypeAbonnement.BASIC:
            return False, "Votre abonnement BASIC ne permet pas d’inviter des membres."

        if self.abonnement.type_abonnement == TypeAbonnement.PRO:
            # Compter les membres invités actifs (excluant le propriétaire lui-même)
            active_members_count = Client.objects.filter(
                tenant=self.tenant,
                role_client=RoleClient.MEMBRE_INVITE,
                user__is_active=True
            ).count()
            if active_members_count >= 2:
                return False, "Vous avez atteint la limite de 2 membres invités pour votre abonnement PROFESSIONNEL."

        # Pour ENTERPRISE, aucune limite n'est appliquée
        return True, ""
    
    def invite_guest(self, email, first_name, last_name, request=None):
        """
        Crée une invitation et un client pour un invité.
        Retourne un tuple (succès, message_erreur, invitation)
        """
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        from .user import User  # Assurez-vous que l'import est correct

        can_invite, message = self.can_invite_guest()
        if not can_invite:
            return False, message, None

        try:
            validate_email(email)
        except ValidationError:
            return False, "Adresse email invalide.", None

        if User.objects.filter(email=email).exists() or Invitation.objects.filter(email=email, status=InvitationStatus.PENDING).exists():
            return False, f"Un utilisateur ou une invitation active existe déjà pour {email}.", None

        try:
            # Création de l'invitation
            invitation = Invitation.objects.create(
                email=email,
                created_by=self.user,
                tenant=self.tenant,
                status=InvitationStatus.PENDING,
                expires_at=timezone.now() + timedelta(days=30)
            )

            # Création du client invité (sans utilisateur actif pour le moment)
            guest_client = Client.objects.create(
                tenant=self.tenant,
                abonnement=self.abonnement,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role_client=RoleClient.MEMBRE_INVITE,
                status=ClientStatus.INVITED,
                invited_by=self.user
            )
            invitation.invited_client = guest_client
            invitation.save()

            self._send_invitation_email(invitation)

            return True, "Invitation envoyée avec succès.", invitation

        except Exception as e:
            # En cas d'erreur, supprimer les objets créés pour éviter les données orphelines
            if 'invitation' in locals() and invitation.pk:
                invitation.delete()
            if 'guest_client' in locals() and guest_client.pk:
                guest_client.delete()
            return False, f"Erreur lors de la création de l'invitation : {str(e)}", None

    def _send_invitation_email(self, invitation):
        from django.conf import settings
        from urllib.parse import quote
        from django.core.mail import send_mail
        import os
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else os.getenv('FRONTEND_URL', 'http://localhost:3000')
        
        # URL de redirection vers la source du client après activation
        redirect_url = "/client/source"  # Vous pouvez personnaliser cette URL
        activation_url = f"{frontend_url}/auth/activation?token={invitation.token}&redirect={quote(redirect_url)}"
        tenant_name = self.tenant.name if self.tenant else 'notre plateforme'
        
        # Préparation du contenu de l'email
        context = {
            'tenant_name': tenant_name,
            'activation_url': activation_url,
            'inviter_name': self.user.get_full_name() if hasattr(self, 'user') and self.user else 'un membre de notre équipe'
        }
        
        # Sujet de l'email
        subject = f"Invitation à rejoindre {tenant_name}"
        
        # Corps de l'email en texte brut
        plain_message = f"""
        Bonjour,
        
        Vous avez été invité à rejoindre {tenant_name} en tant que membre invité.
        Cliquez sur le lien ci-dessous pour activer votre compte et définir votre mot de passe :
        
        {activation_url}
        
        Ce lien expirera dans 7 jours.
        
        Cordialement,
        L'équipe Play Reports
        """
        
        # Envoi de l'email
        try:
            # Essayer d'abord avec le template HTML s'il existe
            try:
                html_message = render_to_string('play_reports/invitation_email.html', context)
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[invitation.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except:
                # Fallback sur l'email en texte brut si le template HTML n'est pas trouvé
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[invitation.email],
                    fail_silently=False,
                )
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email d'invitation : {str(e)}")
            raise