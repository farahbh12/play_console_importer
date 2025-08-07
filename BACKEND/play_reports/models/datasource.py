from django.db import models
from django.utils import timezone

class DataSource(models.Model):
    class SyncStatus(models.TextChoices):
        PENDING = 'pending', 'En attente'
        RUNNING = 'running', 'En cours'
        SUCCESS = 'success', 'Succès'
        ERROR = 'error', 'Erreur'
        WARNING = 'warning', 'Avertissement'

    name = models.CharField(max_length=255, verbose_name="Nom de la source")
    tenant = models.ForeignKey(
        'play_reports.Tenant',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    bucket_uri = models.URLField(max_length=500, verbose_name="URI du bucket")
    status = models.CharField(
    max_length=20,
    choices=SyncStatus.choices,
    default=SyncStatus.PENDING,
    verbose_name="Statut",
    db_column='sync_status'  # <- Ajout ici
)

    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière synchronisation"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    metadata = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name="Métadonnées"
    )

    class Meta:
        # Supprime la ligne db_table pour utiliser le nom par défaut Django (play_reports_datasource)
        verbose_name = "Source de données"
        verbose_name_plural = "Sources de données"
        ordering = ['-created_at']
        unique_together = ['tenant', 'bucket_uri']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def update_status(self, status, save=True):
        """Met à jour le statut de la source de données"""
        self.status = status
        if status == self.SyncStatus.RUNNING:
            self.last_sync = timezone.now()
        if save:
            self.save(update_fields=['status', 'last_sync', 'updated_at'])

    def add_metadata(self, key, value, save=True):
        """Ajoute une métadonnée à la source de données"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
        if save:
            self.save(update_fields=['metadata', 'updated_at'])
