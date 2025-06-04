# ventas/models.py

from django.db import models
from django.contrib.auth.models import User

class Pizzeria(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pizzería"
        verbose_name = "Pizzería"
        verbose_name_plural = "Pizzerías"

    def __str__(self):
        return self.nombre

class DuenoPizzeria(models.Model):
    dueno = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="dueño_id",
        related_name="pizzeria_asignaciones"
    )
    pizzeria = models.ForeignKey(
        Pizzeria,
        on_delete=models.CASCADE,
        db_column="pizzería_id",
        related_name="dueño_asignaciones"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dueño_pizzería"
        unique_together = ("dueno", "pizzeria")
        verbose_name = "Asignación Dueño-Pizzería"
        verbose_name_plural = "Asignaciones Dueño-Pizzería"

    def __str__(self):
        return f"{self.dueno.username} → {self.pizzeria.nombre}"

class Venta(models.Model):
    pizzeria = models.ForeignKey(
        Pizzeria,
        on_delete=models.CASCADE,
        db_column="pizzería_id",
        related_name="ventas"
    )
    dueno = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="dueño_id",
        related_name="ventas_registradas"
    )
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(
        max_length=10,
        choices=[("EFECTIVO", "Efectivo"), ("TARJETA", "Tarjeta"), ("OTRO", "Otro")],
        default="EFECTIVO"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venta"
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Venta #{self.id} ({self.pizzeria.nombre}) - ${self.total}"
