from django.db import models
from django.conf import settings
from ventas.models import Producto, Venta, Pizzeria  # usa tus modelos ya existentes


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


class Receta(models.Model):
    producto = models.ForeignKey(
        Producto,
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
