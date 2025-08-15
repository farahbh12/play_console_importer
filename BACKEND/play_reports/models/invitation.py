import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string

class InvitationStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'
    ACCEPTED = 'ACCEPTED', 'Acceptée'
    REVOKED = 'REVOKED', 'Révoquée'
    EXPIRED = 'EXPIRED', 'Expirée'

class Invitation(models.Model):
    """
    Modèle pour gérer les invitations de membres à accéder aux rapports d'un tenant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name="Email de l'invité")
    token = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField(verbose_name="Date d'expiration")
    status = models.CharField(
        max_length=10,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
        verbose_name="Statut"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name="Créée par"
    )
    # Utilisation de chaînes pour éviter les dépendances circulaires
    tenant = models.ForeignKey(
        'play_reports.Tenant',
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name="Espace client"
    )
    invited_client = models.ForeignKey(
        'play_reports.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitation',
        verbose_name="Client invité"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"
        ordering = ['-created_at']
        unique_together = ('tenant', 'email')

    def __str__(self):
        return f"Invitation pour {self.email} à {self.tenant.name}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(64)
        
        if not self.pk: # S'exécute uniquement à la création
            expiration_days = getattr(settings, 'INVITATION_EXPIRATION_DAYS', 7)
            self.expires_at = timezone.now() + timedelta(days=expiration_days)
            
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Vérifie si la date d'expiration est passée."""
        return timezone.now() > self.expires_at

    @property
    def is_active(self):
        """Vérifie si l'invitation est toujours active."""
        return self.status == InvitationStatus.PENDING and not self.is_expired