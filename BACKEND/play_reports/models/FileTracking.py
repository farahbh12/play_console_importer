from django.db import models

class FileTracking(models.Model):
    """Suivi des fichiers traités."""
    
    tenant_id = models.IntegerField(verbose_name="ID du locataire")
    file_path = models.TextField(verbose_name="Chemin du fichier")
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Empreinte du fichier"
    )
    report_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Type de rapport"
    )
    target_table = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Table cible"
    )
    first_processed = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Premier traitement"
    )
    last_processed = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernier traitement"
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Supprimé"
    )
    
    class Meta:
        db_table = 'file_tracking'
        verbose_name = "Suivi de fichier"
        verbose_name_plural = "Suivis de fichiers"
        unique_together = ['tenant_id', 'file_path']
        indexes = [
            models.Index(fields=['tenant_id', 'file_path']),
            models.Index(fields=['last_processed']),
        ]
    
    def __str__(self):
        return f"{self.file_path} (dernier traitement: {self.last_processed})"