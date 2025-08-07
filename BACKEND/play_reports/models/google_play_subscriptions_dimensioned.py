# google_play_subscriptions_dimensioned.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_subscriptions_dimensioned(models.Model):
    """
    Données d'abonnements Google Play dimensionnées.
    Permet de filtrer les abonnements par différentes dimensions.
    """
    # Types de dimensions
    DIMENSION_TYPES = [
        ('overview', _("Aperçu général")),
        ('country', _("Pays")),
        ('subscription_id', _("ID d'abonnement")),
        ('base_plan_id', _("ID du plan de base")),
        ('offer_id', _("ID de l'offre")),
    ]
    
    # Informations de base
    package_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("Nom du package de l'application")
    )
    
    date = models.DateField(
        db_index=True,
        help_text=_("Date des données d'abonnement")
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
    
    # Statistiques d'abonnement
    new_subscribers = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre de nouveaux abonnés")
    )
    
    cancelled_subscribers = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre d'abonnements annulés")
    )
    
    active_subscribers = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre d'abonnés actifs")
    )
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='subscriptions_dimensioned',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_subscriptions_dimensioned'
        verbose_name = _("Abonnement dimensionné")
        verbose_name_plural = _("Abonnements dimensionnés")
        unique_together = ('tenant', 'package_name', 'date', 'dimension_type', 'dimension_value')
        ordering = ['-date', 'package_name', 'dimension_type', 'dimension_value']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['package_name', 'dimension_type']),
            models.Index(fields=['dimension_type', 'dimension_value']),
        ]

    def __str__(self):
        return f"{self.package_name} - {self.get_dimension_type_display()}: {self.dimension_value} - {self.date}"