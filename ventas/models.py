# ventas/models.py

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q

class Pizzeria(models.Model):
    nombre      = models.CharField(max_length=100)
    direccion   = models.CharField(max_length=200, blank=True, null=True)
    telefono    = models.CharField(max_length=20,  blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pizzeria"
        verbose_name = "Pizzería"
        verbose_name_plural = "Pizzerías"

    def __str__(self):
        return self.nombre


class Venta(models.Model):
    """
    Representa una venta única de una pizzería.
    Ahora incluye:
      - canal: uno de los cuatro canales de venta.
      - método de pago (ya lo tenías).
      - items: relación a VentaProducto (productos vendidos).
    """
    CANALES = [
        ('DOMICILIO',   'Domicilio'),
        ('LLEVAR',      'Llevar'),
        ('MOSTRADOR',   'Mostrador'),
        ('PLATAFORMAS', 'Plataformas'),
        ('DELIVERY',    'Delivery')

    ]

    pizzeria     = models.ForeignKey(
        Pizzeria,
        on_delete=models.CASCADE,
        db_column="pizzeria_id",
        related_name="ventas"
    )
    dueno        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="dueno_id",
        related_name="ventas_registradas"
    )
    #fecha       = models.DateTimeField()
    fecha        = models.DateTimeField(auto_now_add=True)
    total        = models.DecimalField(max_digits=10, decimal_places=2)
    canal        = models.CharField(
        max_length=50,
        choices=CANALES,
        default="MOSTRADOR"
    )
    metodo_pago  = models.CharField(max_length=50, default="EFECTIVO")
    folio_ticket = models.CharField(max_length=50, blank=True, null=True, db_index=True)  
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venta"
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        constraints = [
            models.UniqueConstraint(
                fields=["pizzeria", "folio_ticket"],
                name="uniq_pizzeria_folio",
                condition=Q(folio_ticket__isnull=False) & ~Q(folio_ticket=""),
            ),
        ]
        ordering = ["-fecha"]

    def __str__(self):
        return f"Venta #{self.id} ({self.pizzeria.nombre}) - ${self.total}"


class VentaProducto(models.Model):
    """
    Cada instancia indica que en la Venta X se vendieron Y unidades
    del Producto Z.
    """
    venta     = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name="items"
    )
    producto  = models.ForeignKey(
        "productos.Producto",
        on_delete=models.CASCADE
    )
    cantidad  = models.PositiveIntegerField()

    class Meta:
        db_table = "venta_producto"
        verbose_name = "Item de Venta"
        verbose_name_plural = "Items de Venta"
        #unique_together = ("venta", "producto")

    def __str__(self):
        return f"{self.cantidad}× {self.producto.nombre} en Venta #{self.venta.id}"

class VentaEtapa(models.Model):
    ETAPAS = [
        ("toma_pedido_inicio", "Inicio toma de pedido"),
        ("toma_pedido_fin", "Fin toma de pedido"),
        ("preparacion_inicio", "Inicio preparación"),
        ("preparacion_fin", "Fin preparación"),
        ("envio_inicio", "Inicio envío"),
        ("envio_fin", "Fin envío"),
        ("regreso_repartidor", "Regreso repartidor"),
        ("pago", "Pago realizado"),
        ("cancelada", "Venta cancelada"),
    ]

    venta = models.ForeignKey(
        "Venta",
        on_delete=models.CASCADE,
        related_name="etapas"
    )
    etapa = models.CharField(max_length=30, choices=ETAPAS)
    timestamp = models.DateTimeField(default=now)

    class Meta:
        db_table = "venta_etapa"
        unique_together = ("venta", "etapa")
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.venta.id} - {self.etapa} @ {self.timestamp}"
    