from django.db import models
from django.utils.translation import gettext_lazy as _

class TypeAbonnement(models.TextChoices):
    BASIC = 'BASIC', _('Basic')
    PRO = 'PRO', _('Professionnel')
    ENTERPRISE = 'ENTERPRISE', _('Entreprise')

class Abonnement(models.Model):
    """
    Modèle représentant un type d'abonnement.
    """
    id_abonnement = models.AutoField(primary_key=True)
    
    type_abonnement = models.CharField(
        max_length=20,
        choices=TypeAbonnement.choices,
        unique=True,
        verbose_name=_("Type d'abonnement")
    )
    
    is_active = models.BooleanField(
        default=True, 
        verbose_name=_("Actif")
    )
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Dernière mise à jour")
    )

    class Meta:
        verbose_name = _('Abonnement')
        verbose_name_plural = _('Abonnements')
        ordering = ['type_abonnement']

    def __str__(self):
        return f"{self.id_abonnement} - {self.get_type_abonnement_display()}"