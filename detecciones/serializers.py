import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from .models import Deteccion


class Base64ImageField(serializers.ImageField):
    """
    Custom field that transparently handles both standard multipart file uploads
    and base64-encoded image strings sent within JSON payloads.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.strip():
            # Check for data URI prefix: data:image/jpeg;base64,...
            file_extension = 'jpg'
            if ';base64,' in data:
                header, base64_str = data.split(';base64,', 1)
                if '/' in header:
                    ext = header.split('/')[-1]
                    if ext.lower() in ['jpeg', 'jpg', 'png', 'webp', 'gif']:
                        file_extension = ext.lower()
            else:
                base64_str = data

            try:
                decoded_file = base64.b64decode(base64_str)
            except Exception as e:
                raise serializers.ValidationError(f"Invalid base64-encoded image: {e}")

            file_name = f"captura_{uuid.uuid4().hex[:10]}.{file_extension}"
            data = ContentFile(decoded_file, name=file_name)

        return super().to_internal_value(data)


class DeteccionSerializer(serializers.ModelSerializer):
    """
    Serializer for waste detection event logs submitted from the desktop client.
    Supports file uploads via multipart form data or base64 encoded image strings in JSON.
    Validates confidence scores and normalizes percentage values.
    """
    camara_id = serializers.CharField(required=False, default="CAM_01")
    imagen = Base64ImageField(required=False, allow_null=True)
    imagen_base64 = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Deteccion
        fields = [
            'id',
            'objeto',
            'categoria',
            'confianza',
            'camara_id',
            'imagen',
            'imagen_base64',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']

    def to_internal_value(self, data):
        """
        Normalize payload allowing 'imagen_base64' as an alternative field name for base64 image data.
        """
        if hasattr(data, 'copy'):
            data = data.copy()
        elif isinstance(data, dict):
            data = dict(data)

        if isinstance(data, dict) and 'imagen_base64' in data and not data.get('imagen'):
            data['imagen'] = data.pop('imagen_base64')

        return super().to_internal_value(data)

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