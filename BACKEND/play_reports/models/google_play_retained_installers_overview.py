# google_play_retained_installers_overview.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_retained_installers_overview(models.Model):
    """
    Vue d'ensemble des installateurs retenus.
    Contient les statistiques de rétention des utilisateurs sur différentes périodes.
    """
    # Types de canaux d'acquisition
    ACQUISITION_CHANNEL_CHOICES = [
        ('organic', _('Organique')),
        ('referral', _('Parrainage')),
        ('campaign', _('Campagne')),
        ('search', _('Recherche')),
        ('discovery', _('Découverte')),
        ('external', _('Externe')),
    ]

    # Informations de base
    date = models.DateField(
        db_index=True,
        help_text=_("Date de référence des données")
    )
    
    acquisition_channel = models.CharField(
        max_length=50,
        choices=ACQUISITION_CHANNEL_CHOICES,
        db_index=True,
        help_text=_("Canal d'acquisition des utilisateurs")
    )
    
    country = models.CharField(
        max_length=2,
        db_index=True,
        help_text=_("Code pays ISO 3166-1 alpha-2")
    )
    
    # Détails du trafic
    store_listing_visitors = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre de visiteurs sur la fiche de l'application")
    )
    
    installers = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre d'installations")
    )
    
    visitor_to_installer_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Taux de conversion visiteur → installation (%)")
    )
    
    median_visitor_to_installer = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Médiane du taux de conversion visiteur → installation (%)")
    )
    
    # Métriques de rétention
    installers_retained_1_day = models.PositiveIntegerField(
        default=0,
        help_text=_("Installateurs retenus 1 jour après l'installation")
    )
    
    installers_retained_7_days = models.PositiveIntegerField(
        default=0,
        help_text=_("Installateurs retenus 7 jours après l'installation")
    )
    
    installers_retained_15_days = models.PositiveIntegerField(
        default=0,
        help_text=_("Installateurs retenus 15 jours après l'installation")
    )
    
    installers_retained_30_days = models.PositiveIntegerField(
        default=0,
        help_text=_("Installateurs retenus 30 jours après l'installation")
    )
    
    # Taux de rétention
    retention_rate_1_day = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Taux de rétention à 1 jour (%)")
    )
    
    retention_rate_7_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Taux de rétention à 7 jours (%)")
    )
    
    retention_rate_15_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Taux de rétention à 15 jours (%)")
    )
    
    retention_rate_30_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Taux de rétention à 30 jours (%)")
    )
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='retained_installers_overview',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_retained_installers_overview'
        verbose_name = _("Aperçu des installateurs retenus")
        verbose_name_plural = _("Aperçus des installateurs retenus")
        unique_together = ('tenant', 'date', 'acquisition_channel', 'country')
        ordering = ['-date', 'country', 'acquisition_channel']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['acquisition_channel', 'country']),
            models.Index(fields=['installers']),
            models.Index(fields=['-retention_rate_30_days']),
        ]

    def __str__(self):
        return (f"Installateurs retenus pour {self.country} le {self.date} - "
                f"Canal: {self.get_acquisition_channel_display()}")