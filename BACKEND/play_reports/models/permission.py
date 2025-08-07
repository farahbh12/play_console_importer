from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from rest_framework import permissions


class Permission(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    # Champs ajoutés — assure-toi qu’ils sont bien migrés
    is_for_employee = models.BooleanField(default=True)
    is_for_client = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'

    PERMISSIONS = {
        'invite_report': 'Inviter des membres à voir les rapports',
        # Tu peux ajouter plus de permissions ici
    }

    @classmethod
    def ensure_permissions_exist(cls):
        """Crée les permissions définies si elles n’existent pas déjà."""
        for slug, name in cls.PERMISSIONS.items():
            cls.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'is_for_employee': False,
                    'is_for_client': True
                }
            )

    def __str__(self):
        return self.name


# Création automatique des permissions après chaque migration
@receiver(post_migrate)
def create_default_permissions(sender, **kwargs):
    if sender.name == 'play_reports':
        Permission.ensure_permissions_exist()


# Permission DRF personnalisée
class IsClientOwner(permissions.BasePermission):
    """
    Permission qui vérifie que l’utilisateur est bien le propriétaire du client.
    """
    def has_permission(self, request, view):
        return hasattr(request.user, 'client_profile')

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return True
