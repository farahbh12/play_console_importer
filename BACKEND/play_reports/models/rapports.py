# models.py
from django.db import models
from play_reports.models import Tenant

class Report(models.Model):
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=512)
    size = models.BigIntegerField()
    report_type = models.CharField(max_length=50)
    last_modified = models.DateTimeField()
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.report_type})"