from django.db import models
from django.conf import settings
from ventas.models import Venta, Pizzeria
from productos.models import Producto
from django.utils import timezone
from .utils import convert_qty
from django.core.exceptions import ValidationError



class Insumo(models.Model):
    UNIDADES = [
        ('pieza', 'Pieza'),
        ('gramo', 'Gramo'),
        ('kilogramo', 'Kilogramo'),
        ('litro', 'Litro'),
        ('mililitro', 'Mililitro'),
    ]

    pizzeria = models.ForeignKey(
        Pizzeria,
        on_delete=models.CASCADE,
        related_name='insumos'
    )
    nombre = models.CharField(max_length=100)
    unidad = models.CharField(max_length=20, choices=UNIDADES)
    stock_minimo = models.FloatField(default=0)
    
    #  nuevos
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.pizzeria.nombre})"
    @property
    def stock_actual(self):
        movimientos = self.movimientoinventario_set.all()
        entradas = movimientos.filter(tipo='entrada').aggregate(s=models.Sum('cantidad'))['s'] or 0
        salidas = movimientos.filter(tipo='salida').aggregate(s=models.Sum('cantidad'))['s'] or 0
        ajustes = movimientos.filter(tipo='ajuste').aggregate(s=models.Sum('cantidad'))['s'] or 0
        return entradas - salidas + ajustes

class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]

    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    cantidad = models.FloatField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    unidad = models.CharField(max_length=20)
    pizzeria = models.ForeignKey(Pizzeria, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    motivo = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo.upper()} - {self.insumo.nombre} - {self.cantidad} {self.unidad}"
    
    def clean(self):
        # 1) cantidad > 0
        if self.cantidad is None or self.cantidad <= 0:
            raise ValidationError({"cantidad": "La cantidad debe ser mayor a 0."})

        # 2) pizzería consistente
        if self.insumo_id and self.pizzeria_id != self.insumo.pizzeria_id:
            raise ValidationError("La pizzería del movimiento debe coincidir con la del insumo.")

        # 3) normalizar unidad a la del insumo
        if not self.insumo_id:
            raise ValidationError("Debe especificar un insumo.")
        cantidad_norm = convert_qty(self.cantidad, self.unidad, self.insumo.unidad)

        # 4) si es salida, validar stock suficiente
        if self.tipo == "salida" and self.insumo.stock_actual < cantidad_norm:
            raise ValidationError("Stock insuficiente para la salida solicitada.")

        # 5) aplicar normalización
        self.cantidad = cantidad_norm
        self.unidad = self.insumo.unidad

    def save(self, *args, **kwargs):
        self.full_clean()  # garantiza validaciones siempre
        return super().save(*args, **kwargs)



class Receta(models.Model):
    producto = models.ForeignKey(
        "productos.Producto",
        on_delete=models.CASCADE,
        related_name='recetas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"Receta de {self.producto.nombre}"


class Ingrediente(models.Model):
    receta = models.ForeignKey(
        Receta,
        on_delete=models.CASCADE,
        related_name='ingredientes'
    )
    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.CASCADE
    )
    cantidad = models.FloatField()
    unidad = models.CharField(max_length=20)  # puede ser distinta a la del insumo

    def __str__(self):
        return f"{self.cantidad} {self.unidad} de {self.insumo.nombre} para {self.receta.producto.nombre}"


class SalidaAutomaticaVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    cantidad = models.FloatField()
    unidad = models.CharField(max_length=20)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cantidad} {self.unidad} de {self.insumo.nombre} por Venta #{self.venta.id}"
