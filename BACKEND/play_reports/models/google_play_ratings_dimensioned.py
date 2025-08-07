from django.db import models
from django.utils.translation import gettext_lazy as _

class google_play_ratings_dimensioned(models.Model):
    # Informations de base
    package_name = models.CharField(max_length=255, db_index=True)
    date = models.DateField(db_index=True)

    # ✅ Dimensions optionnelles (une seule remplie par ligne selon le type de CSV)
    app_version = models.CharField(max_length=100, null=True, blank=True)
    carrier = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    device = models.CharField(max_length=100, null=True, blank=True)
    language = models.CharField(max_length=100, null=True, blank=True)
    os_version = models.CharField(max_length=100, null=True, blank=True)

    # ✅ Métriques
    daily_average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)  # ex: 4.16
    total_average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='ratings_dimensioned',
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_ratings_dimensioned'
        unique_together = (
            'tenant', 'package_name', 'date',
            'app_version', 'carrier', 'country',
            'device', 'language', 'os_version',
        )
        indexes = [
            models.Index(fields=['package_name', 'date']),
            models.Index(fields=['app_version']),
            models.Index(fields=['carrier']),
            models.Index(fields=['country']),
            models.Index(fields=['device']),
            models.Index(fields=['language']),
            models.Index(fields=['os_version']),
            models.Index(fields=['total_average_rating']),
        ]
        ordering = ['-date', 'package_name']

    def __str__(self):
        dims = [
            f"app_version={self.app_version}",
            f"carrier={self.carrier}",
            f"country={self.country}",
            f"device={self.device}",
            f"language={self.language}",
            f"os_version={self.os_version}",
        ]
        dim_str = ", ".join([d for d in dims if d.split('=')[1]])
        return f"{self.package_name} - {self.date} - {dim_str} - note={self.total_average_rating}"
