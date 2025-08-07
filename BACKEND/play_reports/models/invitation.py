import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string
from django.core.validators import MinValueValidator

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
    email = models.EmailField(verbose_name="Adresse email du destinataire")
    token = models.CharField(max_length=64, unique=True, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name="Créée par"
    )
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name="Espace client"
    )
    expires_at = models.DateTimeField(verbose_name="Date d'expiration")
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
        verbose_name="Statut"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'tenant'],
                condition=models.Q(status=InvitationStatus.PENDING),
                name='unique_pending_invitation_per_email_tenant'
            )
        ]

    def __str__(self):
        return f"Invitation pour {self.email} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(64)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_active(self):
        return self.status == InvitationStatus.PENDING and not self.is_expired
