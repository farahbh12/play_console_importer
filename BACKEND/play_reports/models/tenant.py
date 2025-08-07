from django.db import models
from django.utils.translation import gettext_lazy as _

class Tenant(models.Model):
    name = models.CharField(max_length=255)
    uri = models.URLField(max_length=512, null=True, blank=True, unique=True)
    is_active = models.BooleanField(default=True, help_text="Indique si le tenant est actif")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'play_reports__tenant'  
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self):
        return self.name
    @property
    def proprietaire(self):
        return self.membres.filter(role_client=RoleClient.OWNER).first()
    
    @property
    def membres_count(self):
        return self.membres.count()
    
    @property
    def membres_invites_count(self):
        return self.membres.filter(role_client=RoleClient.MEMBER).count()
    
    def get_abonnement(self):
        proprietaire = self.proprietaire
        if proprietaire:
            return proprietaire.abonnement
        return None