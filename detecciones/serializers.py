from rest_framework import serializers
from .models import Deteccion


class DeteccionSerializer(serializers.ModelSerializer):
    """
    Serializer for waste detection event logs submitted from the desktop client.
    Validates confidence scores and supports optional image upload.
    """
    camara_id = serializers.CharField(required=False, default="CAM_01")
    imagen = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Deteccion
        fields = [
            'id',
            'objeto',
            'categoria',
            'confianza',
            'camara_id',
            'imagen',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']

    def validate_confianza(self, value):
        """
        Validate confidence score. Normalize if provided as a 0-100 percentage.
        """
        if value < 0.0:
            raise serializers.ValidationError("Confidence must be a non-negative float.")
        if 1.0 < value <= 100.0:
            return round(value / 100.0, 4)
        if value > 100.0:
            raise serializers.ValidationError("Confidence cannot exceed 1.0 (or 100%).")
        return round(value, 4)