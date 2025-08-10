# productos/models.py
from django.db import models

class Producto(models.Model):
    """
    Catálogo de productos que se pueden vender.
    Ahora cada producto pertenece a una Pizzería y tiene:
      - categoria: string
      - descripcion: text (opcional)
      - activo: boolean
    """
    pizzeria    = models.ForeignKey(
        "ventas.Pizzeria",
        on_delete=models.CASCADE,
        related_name="productos"
    )
    nombre      = models.CharField(max_length=100)
    precio      = models.DecimalField(max_digits=8, decimal_places=2)

    categoria   = models.CharField(
        max_length=50,
        help_text="Categoría del producto (ej. Pizza, Bebida, Postre)"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción detallada del producto (opcional)"
    )
    activo      = models.BooleanField(
        default=True,
        help_text="¿Está disponible para la venta?"
    )

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "producto"              # MISMA tabla
        ordering = ["nombre"]              # <- esto hace que no proponga AlterModelOptions
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
    def __str__(self):
        return f"{self.nombre} ({self.pizzeria.nombre})"

