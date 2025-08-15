from rest_framework import serializers
from play_reports.models import Invitation

class InvitationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='invited_client.first_name', read_only=True)
    last_name = serializers.CharField(source='invited_client.last_name', read_only=True)

    class Meta:
        model = Invitation
        fields = ['id', 'email', 'status', 'created_at', 'expires_at', 'first_name', 'last_name']