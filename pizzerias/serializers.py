from rest_framework import serializers
from .models import Pizzeria


# ————————————————————————————————————————————
# Serializador de Pizzería
# ————————————————————————————————————————————
class PizzeriaSerializer(serializers.ModelSerializer):
    total_ventas = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Pizzeria
        fields = ["id", "nombre", "direccion", "telefono", "total_ventas"]
        extra_kwargs = {
            "nombre": {"required": True},
            "direccion": {"required": False, "allow_null": True, "allow_blank": True},
            "telefono": {"required": False, "allow_null": True, "allow_blank": True},
        }

