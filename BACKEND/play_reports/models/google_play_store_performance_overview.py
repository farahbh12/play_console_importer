# google_play_store_performance_overview.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_store_performance_overview(models.Model):
    """
    Vue d'ensemble des performances du Google Play Store.
    Contient les métriques de performance agrégées.
    """
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
    
    # Dimensions
    country = models.CharField(
        max_length=2,
        db_index=True,
        help_text=_("Code pays ISO 3166-1 alpha-2")
    )
    
    traffic_source = models.CharField(
        max_length=100,
        db_index=True,
        help_text=_("Source du trafic (ex: organic, paid, etc.)")
    )
    
    search_term = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Terme de recherche (si applicable)")
    )
    
    utm_source = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Source UTM (si applicable)")
    )
    
    utm_campaign = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Campagne UTM (si applicable)")
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
        related_name='store_performance_overview',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_store_performance_overview'
        verbose_name = _("Performance du Store")
        verbose_name_plural = _("Performances du Store")
        unique_together = (
            'tenant', 'package_name', 'date', 'country', 'traffic_source',
            'search_term', 'utm_source', 'utm_campaign'
        )
        ordering = ['-date', 'package_name', 'country']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['package_name', 'country']),
            models.Index(fields=['traffic_source']),
            models.Index(fields=['search_term']),
            models.Index(fields=['utm_source', 'utm_campaign']),
        ]

    def __str__(self):
        return f"{self.package_name} - {self.date} - {self.country} - {self.traffic_source}"