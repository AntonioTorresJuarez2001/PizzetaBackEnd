from rest_framework import serializers
from .models import Pizzeria, Venta, Producto, VentaProducto, VentaEtapa, UsuarioPizzeriaRol
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

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
    items = VentaProductoSerializer(many=True, required=False)

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
        Si permitir_vacia está en el contexto, se omite esta validación.
        """
        permitir_vacia = self.context.get("permitir_vacia", False)
        if not items and not permitir_vacia:
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
        # Si no viene 'fecha', pon la actual
        if 'fecha' not in validated_data or validated_data['fecha'] is None:
            validated_data['fecha'] = timezone.now()
        # Calcular el total antes de crear la venta
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
        # Validar que no haya etapas críticas ya registradas
        etapas_bloqueo = {"preparacion_inicio", "envio_inicio", "pago"}
        etapas_existentes = set(instance.etapas.values_list("etapa", flat=True))

        if etapas_bloqueo & etapas_existentes:
            raise ValidationError("Esta venta ya no puede ser editada porque ha avanzado en el proceso.")

        # Continúa la lógica normal si se permite editar
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

    def validate(self, data):
        venta = data['venta']
        nueva_etapa = data['etapa']
        etapas_actuales = venta.etapas.values_list('etapa', flat=True)

        if nueva_etapa == 'pago' and 'cancelada' in etapas_actuales:
            raise serializers.ValidationError("No se puede marcar como 'pagada' una venta ya cancelada.")
        
        if nueva_etapa == 'cancelada' and 'pago' in etapas_actuales:
            raise serializers.ValidationError("No se puede cancelar una venta ya marcada como 'pagada'.")
        
        if nueva_etapa in etapas_actuales:
            raise serializers.ValidationError(f"La etapa '{nueva_etapa}' ya ha sido registrada.")

        return data

# Dueños
class UsuarioPizzeriaRolSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    pizzeria = serializers.PrimaryKeyRelatedField(queryset=Pizzeria.objects.all())

    user_display = serializers.StringRelatedField(source="user", read_only=True)
    pizzeria_display = serializers.StringRelatedField(source="pizzeria", read_only=True)

    class Meta:
        model = UsuarioPizzeriaRol
        fields = [
            "id", "user", "pizzeria", "rol", "creado",
            "user_display", "pizzeria_display"
        ]

    def validate(self, data):
        user = data.get("user")
        pizzeria = data.get("pizzeria")

        # Si estamos creando, validar que no exista ya el mismo par user+pizzería
        if not self.instance:
            if UsuarioPizzeriaRol.objects.filter(user=user, pizzeria=pizzeria).exists():
                raise serializers.ValidationError("Ese usuario ya tiene un rol en esa pizzería.")

        # Si estamos actualizando, impedir cambiar el user
        if self.instance and user != self.instance.user:
            raise serializers.ValidationError("No se puede cambiar el usuario asignado.")

        return data