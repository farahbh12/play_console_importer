from django.db import models

class google_play_installs_dimensioned(models.Model):
    # Champs de base
    package_name = models.CharField(max_length=255)
    date = models.DateField()

    # Champs de dimensions (seulement un actif par ligne, selon le fichier)
    country = models.CharField(max_length=100, null=True, blank=True)
    device = models.CharField(max_length=100, null=True, blank=True)
    app_version = models.CharField(max_length=100, null=True, blank=True)
    carrier = models.CharField(max_length=100, null=True, blank=True)
    language = models.CharField(max_length=100, null=True, blank=True)
    os_version = models.CharField(max_length=100, null=True, blank=True)
    android_os_version = models.CharField(max_length=100, null=True, blank=True)


    # Métriques d'installation
    current_device_installs = models.IntegerField(null=True, blank=True, default=0)
    installs_on_active_devices = models.IntegerField(null=True, blank=True, default=0)
    daily_device_installs = models.IntegerField(null=True, blank=True, default=0)
    daily_device_uninstalls = models.IntegerField(null=True, blank=True, default=0)
    daily_device_upgrades = models.IntegerField(null=True, blank=True, default=0)
    total_user_installs = models.IntegerField(null=True, blank=True, default=0)
    daily_user_installs = models.IntegerField(null=True, blank=True, default=0)
    daily_user_uninstalls = models.IntegerField(null=True, blank=True, default=0)

    # Relation avec le locataire
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='installs_dimensioned_data'
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_installs_dimensioned'
        verbose_name = "Google Play Installs Dimensioned"
        verbose_name_plural = "Google Play Installs Dimensioned"
        # Unicité sur base de toutes les colonnes de dimensions
        unique_together = (
            'tenant', 'package_name', 'date',
            'country', 'device', 'app_version',
            'carrier', 'language', 'os_version', 'android_os_version'
        )
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['package_name']),
            models.Index(fields=['country']),
            models.Index(fields=['device']),
            models.Index(fields=['app_version']),
            models.Index(fields=['carrier']),
            models.Index(fields=['language']),
            models.Index(fields=['os_version']),
            models.Index(fields=['android_os_version']),
        ]
        ordering = ['-date', 'package_name']

    def __str__(self):
        dims = [
            f"country={self.country}",
            f"device={self.device}",
            f"app_version={self.app_version}",
            f"carrier={self.carrier}",
            f"language={self.language}",
            f"os_version={self.os_version}",
            f"android_os_version={self.android_os_version}",
        ]
        dim_str = ", ".join([d for d in dims if d.split('=')[1]])
        return f"{self.package_name} - {self.date} - {dim_str}"
