from django.db import models

class google_play_reviews(models.Model):
    # Informations de base
    package_name = models.CharField(max_length=255, db_index=True)
    review_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Informations sur la version
    app_version_code = models.CharField(max_length=50, blank=True, null=True)
    app_version_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Métadonnées du commentaire
    review_title = models.CharField(max_length=500, blank=True, null=True)
    review_text = models.TextField(blank=True, null=True)
    star_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    
    # Dates importantes
    review_submit_date = models.DateTimeField(db_index=True)
    review_submit_millis_since_epoch = models.BigIntegerField(db_index=True)
    review_last_update_date = models.DateTimeField(null=True, blank=True)
    review_last_update_millis_since_epoch = models.BigIntegerField(null=True, blank=True)
    
    # Réponse du développeur
    developer_reply_date = models.DateTimeField(null=True, blank=True)
    developer_reply_millis_since_epoch = models.BigIntegerField(null=True, blank=True)
    developer_reply_text = models.TextField(blank=True, null=True)
    
    # Métadonnées du réviseur
    reviewer_language = models.CharField(max_length=10, blank=True, null=True)
    device = models.CharField(max_length=255, blank=True, null=True)
    device_metadata = models.JSONField(default=dict, blank=True)
    
    # Liens et références
    review_link = models.URLField(max_length=1000, null=True, blank=True)
    
    # Relations
    tenant = models.ForeignKey(
        'Tenant', 
        on_delete=models.CASCADE, 
        related_name='reviews',
        db_index=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_play_reviews'
        verbose_name = "Google Play Review"
        verbose_name_plural = "Google Play Reviews"
        unique_together = ('tenant', 'package_name', 'review_submit_millis_since_epoch')
        indexes = [
            models.Index(fields=['tenant', 'package_name']),
            models.Index(fields=['star_rating']),
            models.Index(fields=['review_submit_date']),
            models.Index(fields=['package_name', 'star_rating']),
        ]
        ordering = ['-review_submit_date']

    def __str__(self):
        return f"Review for {self.package_name} ({self.star_rating}★) - {self.review_submit_date.strftime('%Y-%m-%d')}"