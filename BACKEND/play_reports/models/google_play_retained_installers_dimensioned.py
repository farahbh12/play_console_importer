from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_retained_installers_dimensioned(models.Model):
    """
    Données des installateurs retenus dimensionnées.
    Permet d'analyser la rétention par différentes dimensions.
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

    # Périodes de rétention
    RETENTION_PERIODS = [
        (1, _("1 jour")),
        (7, _("7 jours")),
        (15, _("15 jours")),
        (30, _("30 jours")),
    ]

    # Informations de base
    date = models.DateField(
        db_index=True,
        help_text=_("Date de référence des données")
    )
    
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
    
    # Période de rétention
    retention_period = models.PositiveSmallIntegerField(
        choices=RETENTION_PERIODS,
        db_index=True,
        help_text=_("Période de rétention en jours")
    )
    
    # Métriques de base
    installers = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre total d'installations")
    )
    
    installers_retained = models.PositiveIntegerField(
        default=0,
        help_text=_("Nombre d'installateurs retenus")
    )
    
    retention_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text=_("Taux de rétention (%)")
    )
    
    # Métriques avancées
    median_session_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Durée médiane des sessions (secondes)")
    )
    
    sessions_per_user = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Nombre moyen de sessions par utilisateur")
    )
    
    screen_views_per_session = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Nombre moyen d'écrans vus par session")
    )
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='retained_installers_dimensioned',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_retained_installers_dimensioned'
        verbose_name = _("Installateurs retenus dimensionnés")
        verbose_name_plural = _("Installateurs retenus dimensionnés")
        unique_together = (
            'tenant', 
            'date', 
            'dimension_type', 
            'dimension_value',
            'retention_period'
        )
        ordering = ['-date', 'dimension_type', 'retention_period']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['dimension_type', 'dimension_value']),
            models.Index(fields=['retention_period']),
            models.Index(fields=['retention_rate']),
        ]

    def __str__(self):
        return (
            f"Rétention {self.get_retention_period_display()} - "
            f"{self.get_dimension_type_display()}: {self.dimension_value} - "
            f"Taux: {self.retention_rate}%"
        )

    @property
    def retention_percentage(self):
        """Retourne le taux de rétention formaté en pourcentage"""
        return f"{self.retention_rate}%" if self.retention_rate is not None else "N/A"

    @classmethod
    def get_retention_metrics(cls, tenant, start_date, end_date, dimension_type=None, dimension_value=None):
        """
        Récupère les métriques de rétention avec des filtres optionnels
        """
        queryset = cls.objects.filter(
            tenant=tenant,
            date__range=(start_date, end_date)
        )
        
        if dimension_type:
            queryset = queryset.filter(dimension_type=dimension_type)
        if dimension_value:
            queryset = queryset.filter(dimension_value=dimension_value)
            
        return queryset.order_by('date', 'retention_period')