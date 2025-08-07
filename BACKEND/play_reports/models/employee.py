from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

User = get_user_model()

class RoleEmploye(models.TextChoices):
    ADMINISTRATEUR = 'Administrateur', 'Administrateur'  # Peut tout gérer
    GESTIONNAIRE = 'Gestionnaire', 'Gestionnaire'       # Gestion partielle
       
class Employee(models.Model):
    """
    Modèle représentant un employé avec des droits d'administration.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    first_name = models.CharField(max_length=150, verbose_name='Prénom')
    last_name = models.CharField(max_length=150, verbose_name='Nom')
    role_employe = models.CharField(
        max_length=50,
        choices=RoleEmploye.choices,
        verbose_name='role_employe'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Dernière mise à jour')

    class Meta:
        db_table = 'play_reports_employee'
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'
        ordering = ['last_name', 'first_name']
        permissions = [
            ("manage_employees", "Peut gérer les employés"),
            ("manage_clients", "Peut gérer les clients"),
            ("manage_subscriptions", "Peut gérer les abonnements"),
            ("view_reports", "Peut voir les rapports"),
            ("manage_invitations", "Peut gérer les invitations"),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_employe_display()})"

    @property
    def email(self):
        return self.user.email if self.user else ''

    def get_full_name(self):
        """Retourne le nom complet de l'employé."""
        return f"{self.first_name} {self.last_name}"
    
    def is_administrator(self):
        """Vérifie si l'employé est un administrateur."""
        return self.role_employe == RoleEmploye.ADMINISTRATEUR
    
    def has_permission(self, permission_codename):
        """
        Vérifie si l'employé a une permission spécifique.
        Les administrateurs ont automatiquement toutes les permissions.
        """
        if self.is_administrator():
            return True
            
        # Vérifier si la permission est attribuée via les groupes ou directement
        return self.user.has_perm(f'play_reports.{permission_codename}')
    
    def can_manage_employee(self, target_employee):
        """
        Vérifie si cet employé peut gérer un autre employé.
        Un administrateur peut gérer tout le monde, un gestionnaire ne peut pas gérer les administrateurs.
        """
        if self.is_administrator():
            return True
            
        # Un gestionnaire ne peut pas gérer un administrateur
        if target_employee.is_administrator():
            return False
            
        # Un gestionnaire peut gérer d'autres gestionnaires
        return True
    
    def assign_permission(self, permission_codename):
        """
        Attribue une permission à l'employé.
        """
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Obtenir le content type de l'application
        content_type = ContentType.objects.get_for_model(Employee)
        
        # Obtenir la permission
        try:
            permission = Permission.objects.get(
                content_type=content_type,
                codename=permission_codename
            )
            self.user.user_permissions.add(permission)
            return True
        except Permission.DoesNotExist:
            return False
    
    def remove_permission(self, permission_codename):
        """
        Retire une permission à l'employé.
        """
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Ne pas permettre de retirer des permissions aux administrateurs
        if self.is_administrator():
            return False
            
        # Obtenir le content type de l'application
        content_type = ContentType.objects.get_for_model(Employee)
        
        # Obtenir et retirer la permission
        try:
            permission = Permission.objects.get(
                content_type=content_type,
                codename=permission_codename
            )
            self.user.user_permissions.remove(permission)
            return True
        except (Permission.DoesNotExist, ContentType.DoesNotExist):
            return False