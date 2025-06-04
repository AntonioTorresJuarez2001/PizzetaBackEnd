# ventas/serializers.py

from rest_framework import serializers
from .models import Pizzeria, Venta

class PizzeriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pizzeria
        fields = ["id", "nombre"]

class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = ["id", "fecha", "total"]
