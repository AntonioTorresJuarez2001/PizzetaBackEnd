from rest_framework import serializers
from .models import Pizzeria, Venta, Producto, VentaProducto, VentaEtapa

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


# ————————————————————————————————————————————
# Serializador para cada producto vendido dentro de una venta
# ————————————————————————————————————————————
class VentaProductoSerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    producto_detalle = ProductoSerializer(source='producto', read_only=True)

    class Meta:
        model = VentaProducto
        fields = ['producto', 'producto_detalle', 'cantidad']


# ————————————————————————————————————————————
# Serializador principal de Venta con validaciones y cálculo de total
# ————————————————————————————————————————————
class VentaSerializer(serializers.ModelSerializer):
    canal = serializers.CharField()
    dueno = serializers.HiddenField(default=serializers.CurrentUserDefault())
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
        read_only_fields = ['id', 'dueno', 'fecha', 'total']

    def validate_items(self, items):
        """
        Validar que cada item tenga cantidad > 0 y que el producto esté activo.
        """
        if not items:
            raise serializers.ValidationError("La venta debe contener al menos un producto.")

        for item in items:
            cantidad = item.get('cantidad', 0)
            producto = item.get('producto')

            if cantidad <= 0:
                raise serializers.ValidationError(
                    f"La cantidad para el producto {producto} debe ser mayor a cero."
                )
            if not producto.activo:
                raise serializers.ValidationError(
                    f"El producto '{producto.nombre}' no está activo y no puede ser vendido."
                )
        return items

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])

        # Recalcular total automáticamente ignorando lo enviado por el cliente
        total = sum(
            item['producto'].precio * item['cantidad']
            for item in items_data
        )
        validated_data['total'] = total

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

        if items_data is not None:
            total = sum(
                item['producto'].precio * item['cantidad']
                for item in items_data
            )
            validated_data['total'] = total

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                VentaProducto.objects.create(
                    venta=instance,
                    producto=item['producto'],
                    cantidad=item['cantidad']
                )
        return instance

class VentaEtapaSerializer(serializers.ModelSerializer):
    etapa_display = serializers.CharField(source='get_etapa_display', read_only=True)

    class Meta:
        model = VentaEtapa
        fields = ['id', 'venta', 'etapa', 'etapa_display', 'timestamp']
        read_only_fields = ['id']


