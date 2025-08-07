from django.db import models
from .datasource import DataSource

class DataSourceSyncHistory(models.Model):
    """Historique des synchronisations d'une source de données."""
    
    class Status(models.TextChoices):
        RUNNING = 'running', 'En cours'
        SUCCESS = 'success', 'Succès'
        ERROR = 'error', 'Erreur'
        WARNING = 'warning', 'Avertissement'
    
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,  # Correction ici
        related_name='sync_histories',
        verbose_name="Source de données"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        verbose_name="Statut"
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Début"
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fin"
    )
    log_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Message de journal"
    )
    records_processed = models.PositiveIntegerField(
        default=0,
        verbose_name="Enregistrements traités"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'data_source_sync_history'
        verbose_name = "Historique de synchronisation"
        verbose_name_plural = "Historiques de synchronisation"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Sync {self.get_status_display()} - {self.started_at}"