from django.db import models

class google_play_ratings_overview(models.Model):
    """
    Modèle simplifié de l'aperçu des évaluations Google Play
    avec dimension facultative et relation au tenant.
    """

    # Nom du package (obligatoire)
    package_name = models.CharField(max_length=255, db_index=True)

    # Date du rapport (obligatoire)
    date = models.DateField(db_index=True)

    # Dimension optionnelle (ex: appareil, pays, langue, etc.)
    device = models.CharField(max_length=100, null=True, blank=True)

    # Métriques
    daily_average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    total_average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    # Relation avec le tenant
    tenant = models.ForeignKey(
        'play_reports.Tenant',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_ratings_overview'
        unique_together = ('tenant', 'package_name', 'date', 'device')
        indexes = [
            models.Index(fields=['package_name', 'date']),
            models.Index(fields=['device']),
        ]
        ordering = ['-date', 'package_name']

    def __str__(self):
        return f"{self.package_name} - {self.date} - Note: {self.total_average_rating}"
