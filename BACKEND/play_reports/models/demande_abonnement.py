from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .abonnement import Abonnement

class StatutDemande(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', _('En attente')
    APPROUVEE = 'APPROUVEE', _('Approuvée')
    REJETEE = 'REJETEE', _('Rejetée')

class DemandeChangementAbonnement(models.Model):
    """
    Modèle pour suivre les demandes de changement d'abonnement
    """
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='demandes_changement_abonnement',
        verbose_name=_("Client")
    )
    
    ancien_abonnement = models.ForeignKey(
        Abonnement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anciennes_demandes',
        verbose_name=_("Ancien abonnement")
    )
    
    nouvel_abonnement = models.ForeignKey(
        Abonnement,
        on_delete=models.CASCADE,
        related_name='nouvelles_demandes',
        verbose_name=_("Nouvel abonnement demandé")
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutDemande.choices,
        default=StatutDemande.EN_ATTENTE,
        verbose_name=_("Statut de la demande")
    )
    
    date_demande = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de la demande")
    )
    
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de traitement")
    )
    
    traite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_traitees',
        verbose_name=_("Traité par")
    )
    
    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Commentaire d'administration")
    )
    
    class Meta:
        verbose_name = _('Demande de changement d\'abonnement')
        verbose_name_plural = _('Demandes de changement d\'abonnement')
        ordering = ['-date_demande']
    
    def __str__(self):
        return f"Demande {self.id} - {self.client} ({self.get_statut_display()})"
    
    def save(self, *args, **kwargs):
        # Si c'est une nouvelle demande, enregistrer l'ancien abonnement
        if not self.pk and self.client and self.client.abonnement:
            self.ancien_abonnement = self.client.abonnement
        super().save(*args, **kwargs)
    
    def approuver(self, user, commentaire=None):
        """Approuver la demande de changement d'abonnement"""
        self.statut = StatutDemande.APPROUVEE
        self.traite_par = user
        self.date_traitement = timezone.now()
        self.commentaire = commentaire
        
        # Mettre à jour l'abonnement du client
        self.client.abonnement = self.nouvel_abonnement
        self.client.save()
        
        self.save()
        return True
    
    def rejeter(self, user, commentaire):
        """Rejeter la demande de changement d'abonnement"""
        if not commentaire:
            raise ValueError("Un commentaire est requis pour rejeter une demande")
            
        self.statut = StatutDemande.REJETEE
        self.traite_par = user
        self.date_traitement = timezone.now()
        self.commentaire = commentaire
        self.save()
        return True
