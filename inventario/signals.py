from django.db.models.signals import post_save
from django.dispatch import receiver
from ventas.models import Venta
from inventario.models import Receta, MovimientoInventario, Insumo
from django.db import transaction

@receiver(post_save, sender=Venta)
def descontar_insumos_por_venta(sender, instance, created, **kwargs):
    if not created:
        return

    venta = instance
    pizzeria = venta.pizzeria
    usuario = venta.dueno

    try:
        with transaction.atomic():
            # Validar stock antes de descontar
            for item in venta.items.all():
                producto = item.producto
                cantidad_vendida = item.cantidad

                receta = Receta.objects.filter(producto=producto, activa=True).first()
                if not receta:
                    raise ValueError(f"No hay receta activa para {producto.nombre}")

                for ingrediente in receta.ingredientes.all():
                    insumo = ingrediente.insumo
                    cantidad_total = ingrediente.cantidad * cantidad_vendida

                    if insumo.stock_actual < cantidad_total:
                        raise ValueError(
                            f"Stock insuficiente de {insumo.nombre}. "
                            f"Se requieren {cantidad_total} {ingrediente.unidad}, pero solo hay {insumo.stock_actual}."
                        )

            # Descontar insumos
            for item in venta.items.all():
                producto = item.producto
                cantidad_vendida = item.cantidad
                receta = Receta.objects.filter(producto=producto, activa=True).first()

                for ingrediente in receta.ingredientes.all():
                    insumo = ingrediente.insumo
                    cantidad_total = ingrediente.cantidad * cantidad_vendida

                    MovimientoInventario.objects.create(
                        insumo=insumo,
                        cantidad=cantidad_total,
                        tipo='salida',
                        unidad=ingrediente.unidad,
                        pizzeria=pizzeria,
                        usuario=usuario,
                        motivo=f"Descuento automático por venta de '{producto.nombre}' x{cantidad_vendida}"
                    )

                    # ALERTA: verificar stock mínimo después de descontar
                    if insumo.stock_actual < insumo.stock_minimo:
                        print(
                            f"[ALERTA STOCK BAJO] El insumo '{insumo.nombre}' en la pizzería '{pizzeria.nombre}' "
                            f"ha caído por debajo del mínimo ({insumo.stock_actual} < {insumo.stock_minimo})"
                        )

    except ValueError as e:
        print(f"[ERROR INVENTARIO] {e}")
