# google_play_subscription_cancellation_reasons.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_subscription_cancellation_reasons(models.Model):
    # Types de raisons d'annulation
    CANCELLATION_REASON_CHOICES = [
        ('subscription_canceled', _('Abonnement annulé par l\'utilisateur')),
        ('subscription_canceled_by_system', _('Abonnement annulé par le système')),
        ('subscription_replaced', _('Abonnement remplacé')),
        ('subscription_expired', _('Abonnement expiré')),
        ('subscription_price_change_confirmed', _('Changement de prix confirmé')),
        ('subscription_restarted', _('Abonnement redémarré')),
        ('subscription_revoked', _('Abonnement révoqué')),
        ('subscription_paused', _('Abonnement en pause')),
    ]

    # Informations de base
    cancellation_date = models.DateField(
        db_index=True,
        help_text=_("Date d'annulation de l'abonnement")
    )
    
    package_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("Nom du package de l'application")
    )
    
    subscription_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("ID de l'abonnement")
    )
    
    sku_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_("Identifiant du produit (SKU)")
    )
    
    country = models.CharField(
        max_length=2,
        db_index=True,
        help_text=_("Code pays ISO 3166-1 alpha-2")
    )
    
    # Détails de l'annulation
    cancellation_reason = models.CharField(
        max_length=50,
        choices=CANCELLATION_REASON_CHOICES,
        db_index=True,
        help_text=_("Raison de l'annulation")
    )
    
    cancellation_reason_text = models.TextField(
        blank=True,
        null=True,
        help_text=_("Description détaillée de la raison d'annulation")
    )
    
    cancellation_sub_reason = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Sous-raison de l'annulation")
    )
    
    # Métriques
    cancellation_count = models.PositiveIntegerField(
        default=1,
        help_text=_("Nombre d'annulations pour cette raison")
    )
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='subscription_cancellations',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Date de traitement de l'enregistrement")
    )

    class Meta:
        db_table = 'google_play_subscription_cancellation_reasons'
        verbose_name = _("Raison d'annulation d'abonnement")
        verbose_name_plural = _("Raisons d'annulation d'abonnements")
        unique_together = (
            'tenant', 'package_name', 'cancellation_date', 
            'subscription_id', 'sku_id', 'country', 'cancellation_reason'
        )
        ordering = ['-cancellation_date', 'package_name', 'country']
        indexes = [
            models.Index(fields=['tenant', 'cancellation_date']),
            models.Index(fields=['package_name', 'subscription_id']),
            models.Index(fields=['country', 'cancellation_reason']),
            models.Index(fields=['cancellation_reason', 'cancellation_date']),
        ]