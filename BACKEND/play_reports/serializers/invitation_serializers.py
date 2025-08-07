from rest_framework import serializers
from play_reports.models import Invitation

class InvitationSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'email', 'token', 'status', 'status_display',
            'created_at', 'expires_at', 'is_expired', 'is_active',
            'created_by', 'created_by_name', 'tenant'
        ]
        read_only_fields = ['token', 'created_at', 'created_by', 'tenant']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.email