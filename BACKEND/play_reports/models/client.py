from django.conf import settings
from django.db import models
from play_reports.models.abonnement import Abonnement
import uuid
from datetime import timedelta
from django.utils import timezone

class RoleClient(models.TextChoices):
    OWNER = 'Owner', 'Owner'
    MEMBER = 'Member', 'Membre Invité'

class Client(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_profile'
    )
    role_client = models.CharField(max_length=20, choices=RoleClient.choices, default=RoleClient.OWNER)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
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

    @property
    def is_owner(self):
        return self.role_client == RoleClient.OWNER

    @property
    def is_member(self):
        return self.role_client == RoleClient.MEMBER
        
    def has_permission(self, permission_slug):
        """
        Vérifie si le client a une permission spécifique.
        """
        from django.contrib.auth.models import Permission as AuthPermission
        from django.contrib.contenttypes.models import ContentType
        
        # Les propriétaires ont toutes les permissions
        if self.role_client == 'Owner':
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
        Vérifie si le client peut inviter un membre à voir les rapports.
        Retourne un tuple (bool, str): (peut_inviter, message_erreur)
        """
        # Vérifier si le client a la permission d'inviter
        if not self.has_permission('invite_report'):
            return False, "Vous n'avez pas la permission d'inviter des membres."
        
        # Vérifier l'abonnement
        if not self.abonnement:
            return False, "Aucun abonnement actif."
            
        # Récupérer le nombre d'invitations actives
        from .report_guest import ReportGuest
        active_invites = ReportGuest.objects.filter(
            created_by=self,
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
        
        # Vérifier les limites selon l'abonnement
        if self.abonnement.type_abonnement == 'BASIC':
            return False, "Votre abonnement ne permet pas d'inviter des membres."
        elif self.abonnement.type_abonnement == 'PROFESSIONNEL' and active_invites >= 2:
            return False, "Vous avez atteint la limite de 2 invitations avec votre abonnement PRO."
            
        # Pour ENTERPRISE, pas de limite
        return True, ""
    
    def invite_guest(self, email, request=None):
        """
        Crée une invitation pour un invité.
        Retourne un tuple (succès, message_erreur, invitation)
        """
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        import uuid
        from datetime import timedelta
        from .report_guest import ReportGuest
        
        # Vérifier si l'utilisateur peut inviter
        can_invite, message = self.can_invite_guest()
        if not can_invite:
            return False, message, None
            
        # Valider l'email
        try:
            validate_email(email)
        except ValidationError:
            return False, "Adresse email invalide.", None
            
        # Vérifier si une invitation existe déjà pour cet email
        existing_invite = ReportGuest.objects.filter(
            email=email,
            created_by=self,
            is_active=True,
            expires_at__gt=timezone.now()
        ).first()
        
        if existing_invite:
            return False, f"Une invitation active existe déjà pour {email}", existing_invite
            
        # Créer une nouvelle invitation
        try:
            invitation = ReportGuest.objects.create(
                email=email,
                created_by=self,
                expires_at=timezone.now() + timedelta(days=30)  # Expire dans 30 jours
            )
            
            # Envoyer l'email d'invitation (à implémenter)
            # self._send_invitation_email(invitation, request)
            
            return True, "Invitation envoyée avec succès.", invitation
            
        except Exception as e:
            return False, f"Erreur lors de la création de l'invitation: {str(e)}", None