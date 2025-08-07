# google_play_subscriptions_overview.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_subscriptions_overview(models.Model):
    """
    Vue d'ensemble des abonnements Google Play.
    Contient les statistiques agrégées par produit et pays.
    """
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
    
    product_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("ID du produit d'abonnement")
    )
    
    country = models.CharField(
        max_length=2,
        db_index=True,
        help_text=_("Code pays ISO 3166-1 alpha-2")
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
    
    # Détails de l'offre
    base_plan_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("ID du plan de base")
    )
    
    offer_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("ID de l'offre promotionnelle")
    )
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='subscriptions_overview',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_subscriptions_overview'
        verbose_name = _("Aperçu des abonnements")
        verbose_name_plural = _("Aperçus des abonnements")
        unique_together = ('tenant', 'package_name', 'date', 'product_id', 'country')
        ordering = ['-date', 'package_name', 'country']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['package_name', 'product_id']),
            models.Index(fields=['country']),
            models.Index(fields=['base_plan_id']),
            models.Index(fields=['offer_id']),
        ]

    def __str__(self):
        return f"{self.package_name} - {self.product_id} - {self.country} - {self.date}"