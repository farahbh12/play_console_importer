from rest_framework import serializers

def create_dynamic_serializer(model_class):
    """Crée une classe de sérialiseur ModelSerializer à la volée pour un modèle donné."""
    class DynamicSerializer(serializers.ModelSerializer):
        class Meta:
            model = model_class
            fields = '__all__'
    return DynamicSerializer
