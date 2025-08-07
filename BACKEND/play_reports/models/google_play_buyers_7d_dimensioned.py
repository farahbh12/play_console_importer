# google_play_buyers_dimensioned.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_buyers_7d_dimensioned(models.Model):
    """
    Données des acheteurs dimensionnées.
    Permet de filtrer les performances d'acquisition par différentes dimensions.
    """
    # Types de dimensions
    DIMENSION_TYPES = [
        ('overview', _("Aperçu général")),
        ('country', _("Pays")),
        ('acquisition_channel', _("Canal d'acquisition")),
        ('utm_source', _("Source UTM")),
        ('utm_campaign', _("Campagne UTM")),
        ('keyword', _("Mot-clé")),
    ]

    # Informations de base
    date = models.DateField(
        db_index=True,
        help_text=_("Date de début de la période de 7 jours")
    )
    
    # Détails de la dimension
    dimension_type = models.CharField(
        max_length=20,
        choices=DIMENSION_TYPES,
        db_index=True,
        help_text=_("Type de dimension")
    )
    
    dimension_value = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("Valeur de la dimension")
    )
    
    # Métriques
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
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='buyers_dimensioned',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_buyers_dimensioned'
        verbose_name = _("Acheteurs dimensionnés 7j")
        verbose_name_plural = _("Acheteurs dimensionnés 7j")
        unique_together = ('tenant', 'date', 'dimension_type', 'dimension_value')
        ordering = ['-date', 'dimension_type', 'dimension_value']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['dimension_type', 'dimension_value']),
            models.Index(fields=['buyers']),
        ]