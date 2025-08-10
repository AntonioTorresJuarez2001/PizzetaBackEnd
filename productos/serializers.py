from productos.models import Producto
from rest_framework import serializers


# ————————————————————————————————————————————
# Serializador de Producto
# ————————————————————————————————————————————
class ProductoSerializer(serializers.ModelSerializer):
    pizzeria = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'nombre',
            'precio',
            'categoria',
            'descripcion',
            'activo',
            'pizzeria',
            'created_at',
        ]
        extra_kwargs = {
            'categoria': {'required': True, 'allow_blank': False},
            'descripcion': {'required': False, 'allow_blank': True},
            'activo': {'required': True},
        }

