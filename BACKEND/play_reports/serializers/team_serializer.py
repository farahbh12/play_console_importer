from rest_framework import serializers
from django.contrib.auth import get_user_model
from play_reports.models import Client, Invitation, InvitationStatus

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour les informations de base de l'utilisateur.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']

class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'user', 'role_client', 'status']

    def get_status(self, obj):
        if obj.user and obj.user.is_active:
            return 'Active'
        return 'Inactive'
