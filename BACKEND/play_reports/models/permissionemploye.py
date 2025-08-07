from django.db import models
from django.core.exceptions import ValidationError

class PermissionEmploye(models.Model):
    """
    Modèle de liaison entre une permission, un abonnement et un employé.
    Définit quelles permissions sont attribuables à un employé en fonction de son abonnement.
    """
    permission = models.ForeignKey(
        'Permission', 
        on_delete=models.CASCADE,
        related_name='employee_permissions',
        verbose_name='Permission'
    )
    abonnement = models.ForeignKey(
        'Abonnement', 
        on_delete=models.CASCADE, 
        related_name='employee_permissions',
        verbose_name="Abonnement"
    )
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='permissions',
        verbose_name='Employé',
        null=True,
        blank=True
    )
    granted_by = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        related_name='granted_permissions',
        verbose_name='Attribuée par',
        null=True,
        blank=True
    )
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'attribution')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    class Meta:
        verbose_name = 'Permission employé'
        verbose_name_plural = 'Permissions employés'
        unique_together = ('permission', 'employee')
        ordering = ['permission__name']

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.permission.name} - {self.employee} ({status})"

    def clean(self):
        """
        Validation personnalisée pour s'assurer que l'employé qui attribue la permission
        a le droit de le faire.
        """
        # Si c'est une nouvelle instance ou que l'employé a changé
        if not self.pk or (self.pk and self.employee_id != self.__class__.objects.get(pk=self.pk).employee_id):
            # Un administrateur ne peut pas se modifier lui-même
            if self.employee and self.employee.role_employe == 'Administrateur' and not getattr(self, '_force_save', False):
                raise ValidationError({
                    'employee': 'Impossible de modifier les permissions d\'un administrateur.'
                })
            
            # Vérifier que l'abonnement permet cette permission
            if not self.permission.is_for_employee:
                raise ValidationError({
                    'permission': 'Cette permission ne peut pas être attribuée à un employé.'
                })
            
            # Vérifier que l'employé qui accorde la permission a le droit de le faire
            if hasattr(self, 'granted_by') and self.granted_by:
                if not self.granted_by.can_manage_employees():
                    raise ValidationError({
                        'granted_by': 'Vous n\'êtes pas autorisé à accorder cette permission.'
                    })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Mettre à jour les permissions de l'utilisateur
        if self.employee and hasattr(self.employee, 'user'):
            if self.is_active:
                self.employee.user.user_permissions.add(self.permission.django_permission)
            else:
                self.employee.user.user_permissions.remove(self.permission.django_permission)

    def delete(self, *args, **kwargs):
        # Retirer la permission avant la suppression
        if self.employee and hasattr(self.employee, 'user'):
            self.employee.user.user_permissions.remove(self.permission.django_permission)
        super().delete(*args, **kwargs)

    @classmethod
    def get_available_permissions(cls, abonnement):
        """
        Retourne les permissions disponibles pour un abonnement donné.
        """
        return cls.objects.filter(
            abonnement=abonnement,
            is_active=True
        ).select_related('permission')

    @classmethod
    def get_employee_permissions(cls, employee):
        """
        Retourne toutes les permissions actives d'un employé.
        """
        return cls.objects.filter(
            employee=employee,
            is_active=True
        ).select_related('permission', 'abonnement')
