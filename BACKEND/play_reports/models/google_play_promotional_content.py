# google_play_promotional_content.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_promotional_content(models.Model):
    """
    Modèle pour suivre les performances du contenu promotionnel sur Google Play.
    """
    # Types de résultats possibles
    OUTCOME_CHOICES = [
        ('view', _('Vue')),
        ('click', _('Clic')),
        ('install', _('Installation')),
        ('purchase', _('Achat')),
    ]

    # Informations de base
    promotional_content_id = models.CharField(
        max_length=100,
        help_text=_("Identifiant unique du contenu promotionnel")
    )
    
    promotional_content_name = models.CharField(
        max_length=255,
        help_text=_("Nom du contenu promotionnel")
    )
    
    package_name = models.CharField(
        max_length=255,
        help_text=_("Nom du package de l'application")
    )
    
    date = models.DateField(
        db_index=True,
        help_text=_("Date des statistiques")
    )
    
    country = models.CharField(
        max_length=2,
        db_index=True,
        help_text=_("Code pays ISO 3166-1 alpha-2")
    )
    
    outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES,
        db_index=True,
        help_text=_("Type de résultat mesuré")
    )
    
    # Métriques quotidiennes
    daily_converters = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre de convertisseurs quotidiens")
    )
    
    daily_conversion_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Taux de conversion quotidien (%)")
    )
    
    # Métriques sur 28 jours
    rolling_28d_converters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Moyenne mobile sur 28 jours des convertisseurs")
    )
    
    rolling_28d_viewers = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Moyenne mobile sur 28 jours des vues uniques")
    )
    
    rolling_28d_conversion_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Taux de conversion moyen sur 28 jours (%)")
    )
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='promotional_contents',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_promotional_content'
        verbose_name = _("Contenu promotionnel")
        verbose_name_plural = _("Contenus promotionnels")
        unique_together = (
            'tenant', 
            'promotional_content_id', 
            'date', 
            'country',
            'outcome'
        )
        ordering = ['-date', 'country', 'promotional_content_name']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['promotional_content_id']),
            models.Index(fields=['country']),
            models.Index(fields=['outcome']),
            models.Index(fields=['package_name']),
        ]

    def __str__(self):
        return (
            f"{self.promotional_content_name} ({self.country}) - "
            f"{self.date} - {self.get_outcome_display()}"
        )

    @property
    def content_identifier(self):
        """Retourne un identifiant lisible pour le contenu"""
        return f"{self.promotional_content_name} ({self.promotional_content_id})"

    @classmethod
    def get_content_performance(cls, tenant, start_date, end_date, content_id=None, country=None):
        """
        Récupère les performances du contenu promotionnel avec des filtres optionnels
        """
        queryset = cls.objects.filter(
            tenant=tenant,
            date__range=(start_date, end_date)
        )
        
        if content_id:
            queryset = queryset.filter(promotional_content_id=content_id)
        if country:
            queryset = queryset.filter(country=country)
            
        return queryset.order_by('date', 'country', 'outcome')