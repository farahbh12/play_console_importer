from django.db import models
from django.utils import timezone

class google_play_installs_overview(models.Model):
    # Champs de base
    package_name = models.CharField(max_length=255)
    date = models.DateField()
    
    # Champs de dimension (peuvent être NULL)
    device = models.CharField(max_length=255, blank=True, null=True, default='')
    app_version = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)

    # Métriques d'installation
    current_device_installs = models.IntegerField(null=True, blank=True, default=0)
    installs_on_active_devices = models.IntegerField(null=True, blank=True, default=0)
    daily_device_installs = models.IntegerField(null=True, blank=True, default=0)
    daily_device_uninstalls = models.IntegerField(null=True, blank=True, default=0)
    daily_device_upgrades = models.IntegerField(null=True, blank=True, default=0)
    total_user_installs = models.IntegerField(null=True, blank=True, default=0)
    daily_user_installs = models.IntegerField(null=True, blank=True, default=0)
    daily_user_uninstalls = models.IntegerField(null=True, blank=True, default=0)

    # Relations
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='installs_overview_data'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_installs_overview'
        verbose_name = "Google Play Installs Overview"
        verbose_name_plural = "Google Play Installs Overview"
        unique_together = (
            'tenant', 'package_name', 'date', 'device', 
            'app_version', 'os_version', 'country', 'language', 'carrier'
        )
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['package_name']),
            models.Index(fields=['device']),
            models.Index(fields=['app_version']),
            models.Index(fields=['os_version']),
            models.Index(fields=['country']),
            models.Index(fields=['language']),
            models.Index(fields=['carrier']),
        ]
        ordering = ['-date', 'package_name']

    def __str__(self):
        return f"{self.package_name} - {self.date} - {self.device or 'All Devices'}"