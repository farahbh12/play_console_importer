from django.db import models

class google_play_crashes_overview(models.Model):
    package_name = models.CharField(max_length=255)
    date = models.DateField()
    
    # Champs de dimension
    device = models.CharField(max_length=255, blank=True, null=True)
    app_version = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=100, blank=True, null=True)
    android_os_version = models.CharField(max_length=100, blank=True, null=True)

    # Métriques
    daily_crashes = models.IntegerField(default=0)
    daily_anrs = models.IntegerField(null=True, blank=True, default=0)

    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='crashes_overview_data'
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_crashes_overview'
        verbose_name = "Google Play Crashes Overview"
        verbose_name_plural = "Google Play Crashes Overview"
        unique_together = (
            'tenant', 'package_name', 'date', 
            'device', 'app_version', 'os_version', 'android_os_version'
        )
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['package_name']),
            models.Index(fields=['device']),
            models.Index(fields=['app_version']),
            models.Index(fields=['os_version']),
            models.Index(fields=['android_os_version']),
        ]
        ordering = ['-date', 'package_name']

    def __str__(self):
        return (
            f"Crash {self.package_name} - {self.date} - "
            f"{self.device or 'All Devices'} - {self.app_version or 'All Versions'}"
        )