from rest_framework import serializers
from django.db import IntegrityError, transaction
from .models import Venta, VentaProducto, VentaEtapa
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from productos.models import Producto
from productos.serializers import ProductoSerializer


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
            'folio_ticket'
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
        if not validated_data.get('fecha'):
            validated_data['fecha'] = timezone.now()

        # Calcular el total antes de crear la venta
        total = sum(item['producto'].precio * item['cantidad'] for item in items_data)
        validated_data['total'] = total

        # Si el serializer permite folio_ticket, tómalo de validated_data; si no, de initial_data
        provided_folio = validated_data.pop('folio_ticket', None)
        if provided_folio is None:
            provided_folio = self.initial_data.get('folio_ticket')

        try:
            with transaction.atomic():
                # Crear la venta primero (sin items)
                venta = Venta.objects.create(**validated_data)

                # Asignar folio (o generar uno basado en el id)
                folio = provided_folio or str(venta.id)
                venta.folio_ticket = folio
                venta.save(update_fields=['folio_ticket'])  # valida unicidad por pizzería

                # Crear items sólo si el folio fue aceptado por la BD
                for item in items_data:
                    VentaProducto.objects.create(
                        venta=venta,
                        producto=item['producto'],
                        cantidad=item['cantidad'],
                    )

                return venta

        except IntegrityError:
            raise serializers.ValidationError(
                {"folio_ticket": "Este folio ya existe en esta pizzería."}
            )


    def update(self, instance, validated_data):
        # Validar etapas críticas
        etapas_bloqueo = {"preparacion_inicio", "envio_inicio", "pago"}
        etapas_existentes = set(instance.etapas.values_list("etapa", flat=True))

        if etapas_bloqueo & etapas_existentes:
            raise ValidationError("Esta venta ya no puede ser editada porque ha avanzado en el proceso.")

        # Continúa la lógica normal si se permite editar
        items_data = validated_data.pop('items', None)

        if items_data is not None:
            total = sum(item['producto'].precio * item['cantidad'] for item in items_data)
            validated_data['total'] = total

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        try:
            with transaction.atomic():
                instance.save()  # aquí valida unicidad del folio

                if items_data is not None:
                    instance.items.all().delete()
                    for item in items_data:
                        instance.items.create(
                            producto=item['producto'],
                            cantidad=item['cantidad']
                        )
        except IntegrityError:
            raise serializers.ValidationError(
                {"folio_ticket": "Este folio ya existe en esta pizzería."}
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
