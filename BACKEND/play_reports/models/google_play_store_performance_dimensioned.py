# google_play_store_performance_dimensioned.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_store_performance_dimensioned(models.Model):
    """
    Données de performance du Google Play Store dimensionnées.
    Permet de filtrer les performances par différentes dimensions.
    """
    # Types de dimensions
    DIMENSION_TYPES = [
        ('overview', _("Aperçu général")),
        ('country', _("Pays")),
        ('traffic_source', _("Source de trafic")),
        ('search_term', _("Terme de recherche")),
        ('utm_source', _("Source UTM")),
        ('utm_campaign', _("Campagne UTM")),
    ]
    
    # Informations de base
    package_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("Nom du package de l'application")
    )
    
    date = models.DateField(
        db_index=True,
        help_text=_("Date des données de performance")
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
    
    # Métriques de performance
    store_listing_visitors = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre de visiteurs sur la fiche de l'application")
    )
    
    store_listing_acquisitions = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre d'acquisitions depuis la fiche")
    )
    
    store_listing_conversion_rate = models.FloatField(null=True, blank=True)


    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='store_performance_dimensioned',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_store_performance_dimensioned'
        verbose_name = _("Performance du Store dimensionnée")
        verbose_name_plural = _("Performances du Store dimensionnées")
        unique_together = ('tenant', 'package_name', 'date', 'dimension_type', 'dimension_value')
        ordering = ['-date', 'package_name', 'dimension_type', 'dimension_value']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['package_name', 'dimension_type']),
            models.Index(fields=['dimension_type', 'dimension_value']),
        ]

    def __str__(self):
        return f"{self.package_name} - {self.get_dimension_type_display()}: {self.dimension_value} - {self.date}"

    @property
    def conversion_rate_percentage(self):
        """Retourne le taux de conversion en pourcentage formaté"""
        return f"{self.store_listing_conversion_rate}%"