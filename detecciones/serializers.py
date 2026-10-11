from rest_framework import serializers
from .models import Deteccion

class DeteccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deteccion
        fields = '__all__'