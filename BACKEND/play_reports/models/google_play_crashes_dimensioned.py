from django.db import models

class google_play_crashes_dimensioned(models.Model):
    # Champs de base
    package_name = models.CharField(max_length=255)
    date = models.DateField()

    # Champs de dimensions (un seul actif par ligne)
    app_version = models.CharField(max_length=100, null=True, blank=True)
    device = models.CharField(max_length=100, null=True, blank=True)
    os_version = models.CharField(max_length=100, null=True, blank=True)
    android_os_version = models.CharField(max_length=100, null=True, blank=True)

    # Métriques de crash
    daily_crashes = models.IntegerField(default=0)
    daily_anrs = models.IntegerField(null=True, blank=True, default=0)
    crash_rate = models.FloatField(null=True, blank=True)
    anr_rate = models.FloatField(null=True, blank=True)

    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='crashes_dimensioned_data'
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_crashes_dimensioned'
        verbose_name = "Google Play Crashes Dimensioned"
        verbose_name_plural = "Google Play Crashes Dimensioned"
        unique_together = (
            'tenant', 'package_name', 'date',
            'app_version', 'device', 'os_version', 'android_os_version'
        )
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['package_name']),
            models.Index(fields=['app_version']),
            models.Index(fields=['device']),
            models.Index(fields=['os_version']),
            models.Index(fields=['android_os_version']),
        ]
        ordering = ['-date', 'package_name']

    def __str__(self):
        dims = [
            f"app_version={self.app_version}",
            f"device={self.device}",
            f"os_version={self.os_version}",
            f"android_os_version={self.android_os_version}",
        ]
        dim_str = ", ".join([d for d in dims if d.split('=')[1]])
        return f"{self.package_name} - {self.date} - {dim_str}"
