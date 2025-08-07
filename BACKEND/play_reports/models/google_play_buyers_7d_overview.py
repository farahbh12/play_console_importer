# google_play_buyers_overview.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_buyers_7d_overview(models.Model):
    """
    Vue d'ensemble des acheteurs sur 7 jours.
    Contient les statistiques agrégées sur une période de 7 jours.
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
        help_text=_("Date de début de la période de 7 jours")
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
    
    buyers = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre d'acheteurs uniques")
    )
    
    repeat_buyers = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre d'acheteurs récurrents")
    )
    
    # Taux de conversion
    visitor_to_installer_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Taux de conversion visiteur → installation (%)")
    )
    
    installer_to_buyer_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Taux de conversion installation → achat (%)")
    )
    
    buyer_to_repeat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Taux de réachat (%)")
    )
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='buyers_overview',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_buyers_overview'
        verbose_name = _("Aperçu des acheteurs 7j")
        verbose_name_plural = _("Aperçus des acheteurs 7j")
        unique_together = ('tenant', 'date', 'acquisition_channel', 'country')
        ordering = ['-date', 'country', 'acquisition_channel']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['acquisition_channel', 'country']),
            models.Index(fields=['store_listing_visitors']),
            models.Index(fields=['buyers']),
        ]