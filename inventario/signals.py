from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from collections import defaultdict
import logging

from ventas.models import Venta
from inventario.models import Receta, MovimientoInventario, Insumo, SalidaAutomaticaVenta
from inventario.utils import convert_qty


@receiver(post_save, sender=Venta)
def descontar_insumos_por_venta(sender, instance, created, **kwargs):
    if not created:
        return

    venta = instance
    pizzeria = venta.pizzeria
    usuario = getattr(venta, "dueno", None)

    try:
        with transaction.atomic():
            # ----- 1) Recolectar items y recetas en bloque (evita N+1)
            items = list(venta.items.select_related("producto").all())
            if not items:
                logging.info("Venta %s sin items; no hay descuento de inventario.", venta.id)
                return

            producto_ids = [it.producto_id for it in items]
            recetas = {
                r.producto_id: r
                for r in Receta.objects.filter(producto_id__in=producto_ids, activa=True)
                .prefetch_related("ingredientes__insumo")
            }

            # ----- 2) Sumar requeridos por insumo (ya convertidos a la unidad del insumo)
            requeridos = defaultdict(float)  # insumo_id -> cantidad total requerida
            for it in items:
                receta = recetas.get(it.producto_id)
                if not receta:
                    raise ValueError(f"No hay receta activa para {it.producto.nombre}")
                for ing in receta.ingredientes.all():
                    insumo = ing.insumo
                    req = convert_qty(ing.cantidad * it.cantidad, ing.unidad, insumo.unidad)
                    requeridos[insumo.id] += req

            insumo_ids = list(requeridos.keys())
            if not insumo_ids:
                logging.info("Venta %s sin ingredientes en recetas; no hay descuento.", venta.id)
                return

            # ----- 3) Bloqueo de insumos (con orden para minimizar deadlocks)
            insumos = (Insumo.objects
                       .select_for_update()
                       .filter(id__in=insumo_ids)
                       .order_by("id"))

            # Validar stock disponible
            for insumo in insumos:
                req = requeridos.get(insumo.id, 0.0)
                if insumo.stock_actual < req:
                    raise ValueError(
                        f"Stock insuficiente de {insumo.nombre}. "
                        f"Requerido: {req} {insumo.unidad}, disponible: {insumo.stock_actual}."
                    )

            # ----- 4) Crear movimientos y salida auditada
            for it in items:
                receta = recetas[it.producto_id]
                for ing in receta.ingredientes.all():
                    insumo = ing.insumo
                    cant_total = convert_qty(ing.cantidad * it.cantidad, ing.unidad, insumo.unidad)

                    mov = MovimientoInventario.objects.create(
                        insumo=insumo,
                        cantidad=cant_total,
                        tipo="salida",
                        unidad=insumo.unidad,  # el modelo igual normaliza
                        pizzeria=pizzeria,
                        usuario=usuario,
                        motivo=f"Descuento por venta '{it.producto.nombre}' x{it.cantidad} (venta #{venta.id})",
                    )

                    SalidaAutomaticaVenta.objects.create(
                        venta=venta,
                        insumo=insumo,
                        cantidad=cant_total,
                        unidad=insumo.unidad,
                    )

            # ----- 5) Alertas de stock bajo (una vez por insumo, ya descontado)
            for insumo in insumos:
                if insumo.stock_actual < insumo.stock_minimo:
                    logging.warning(
                        "STOCK BAJO: %s en '%s' (%.3f < %.3f)",
                        insumo.nombre, pizzeria.nombre, insumo.stock_actual, insumo.stock_minimo
                    )

    except ValueError as e:
        # Decide: si quieres que la petición de creación de venta falle:
        logging.error("INVENTARIO - Venta %s: %s", getattr(venta, "id", "?"), e)
        # raise  # <- descomenta si quieres cortar la petición y hacer rollback si estás dentro de una tx mayor
        # Si prefieres no romper la creación de la venta, deja solo el log.
