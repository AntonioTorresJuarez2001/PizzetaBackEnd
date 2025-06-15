# ventas/serializers.py

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import Pizzeria, Venta, Producto, VentaProducto

# ————————————————————————————————————————————————————————————————
# 1) Serializador de Pizzería (igual que antes)
# ————————————————————————————————————————————————————————————————
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


# ————————————————————————————————————————————————————————————————
# 2) Serializadores nuevos para Producto y VentaProducto
# ————————————————————————————————————————————————————————————————
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


class VentaProductoSerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    producto_detalle = ProductoSerializer(source='producto', read_only=True)

    class Meta:
        model = VentaProducto
        fields = ['producto', 'producto_detalle', 'cantidad']


# ————————————————————————————————————————————————————————————————
# 3) Serializador de Venta extendido
# ————————————————————————————————————————————————————————————————
class VentaSerializer(serializers.ModelSerializer):
    # Nuevo campo canal (asegúrate de definir CANALES en tu modelo Venta)
    canal = serializers.ChoiceField(choices=Venta.CANALES, required=True)
    # Anidado: las líneas de producto
    items = VentaProductoSerializer(many=True)

    class Meta:
        model = Venta
        fields = [
            'id',
            'dueno',
            'fecha',
            'total',
            'canal',
            'metodo_pago',
            'items',
        ]
        read_only_fields = ['id', 'dueno', 'fecha']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        # pizzeria y dueno los inyecta la vista en perform_create
        venta = Venta.objects.create(**validated_data)
        for item in items_data:
            VentaProducto.objects.create(
                venta=venta,
                producto=item['producto'],
                cantidad=item['cantidad']
            )
        return venta

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Actualizar campos básicos
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if items_data is not None:
            # Reemplazar todas las líneas
            instance.items.all().delete()
            for item in items_data:
                VentaProducto.objects.create(
                    venta=instance,
                    producto=item['producto'],
                    cantidad=item['cantidad']
                )
        return instance
