from django.db import models
from django.conf import settings
from ventas.models import Venta
from pizzerias.models import Pizzeria
from productos.models import Producto
from django.utils import timezone
from .utils import convert_qty
from django.core.exceptions import ValidationError
from django.db import transaction



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

# --- SUB-RECETAS (fórmula que produce un INSUMO) ---

class FormulaInsumo(models.Model):
    """
    Define cómo producir un Insumo objetivo (p. ej., 'Masa') a partir de otros insumos.
    Las cantidades de ingredientes están definidas por 1 unidad de salida.
    """
    insumo_objetivo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name="formulas")
    activa = models.BooleanField(default=True)
    factor_rendimiento_esperado = models.FloatField(default=1.0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Fórmula de {self.insumo_objetivo.nombre} (activa={self.activa})"


class FormulaIngrediente(models.Model):
    formula = models.ForeignKey(FormulaInsumo, on_delete=models.CASCADE, related_name="ingredientes")
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    cantidad = models.FloatField()              # por 1 unidad de salida
    unidad = models.CharField(max_length=20)    # puede diferir de la del insumo

    def __str__(self):
        return f"{self.cantidad} {self.unidad} de {self.insumo.nombre} (por 1 unidad de salida)"


class LoteProduccion(models.Model):
    """
    Ejecuta una producción: descuenta insumos base y genera entrada del insumo objetivo.
    El usuario indicará el 'rendimiento_real' al confirmar.
    """
    pizzeria = models.ForeignKey(Pizzeria, on_delete=models.CASCADE)
    formula = models.ForeignKey(FormulaInsumo, on_delete=models.PROTECT, related_name="lotes")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    cantidad_objetivo = models.FloatField()          # cuántas unidades de salida planeas producir (p. ej., 1.0 kg)
    unidad_objetivo = models.CharField(max_length=20, choices=Insumo.UNIDADES) # debe ser la unidad del insumo objetivo

    rendimiento_real = models.FloatField(null=True, blank=True)  # lo que pese realmente (lo pone el usuario)
    fecha = models.DateTimeField(auto_now_add=True)
    confirmado = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.formula and (self.unidad_objetivo or "").strip().lower() != (self.formula.insumo_objetivo.unidad or "").strip().lower():
            raise ValidationError("La unidad del lote debe coincidir con la del insumo objetivo.")
        # opcional: normaliza
        self.unidad_objetivo = (self.unidad_objetivo or "").strip().lower()
        if self.cantidad_objetivo is None or self.cantidad_objetivo <= 0:
            raise ValidationError("La cantidad objetivo debe ser mayor a 0.")

    def __str__(self):
        return f"Lote {self.id} de {self.formula.insumo_objetivo.nombre}"

def ejecutar_lote_produccion(lote: LoteProduccion, rendimiento_real: float | None = None):
    if lote.confirmado:
        raise ValidationError("El lote ya está confirmado.")
    formula = lote.formula
    insumo_obj = formula.insumo_objetivo

    # 1) Determinar rendimiento real (prioridad: lo que manda el usuario ahora)
    rendimiento = rendimiento_real or lote.rendimiento_real
    if rendimiento is None:
        # fallback opcional con esperado (si no quieres permitir, lanza error)
        rendimiento = lote.cantidad_objetivo * (formula.factor_rendimiento_esperado or 1.0)
    if rendimiento <= 0:
        raise ValidationError("Debes indicar un rendimiento_real mayor a 0.")

    # 2) Validaciones de unidad
    if lote.unidad_objetivo != insumo_obj.unidad:
        raise ValidationError("La unidad del lote no coincide con la del insumo objetivo.")

    with transaction.atomic():
        # 3) Salidas por ingredientes (escala por cantidad_objetivo)
        for ing in formula.ingredientes.select_related("insumo").all():
            insumo_ing = ing.insumo
            cant_total = ing.cantidad * lote.cantidad_objetivo
            cant_norm = convert_qty(cant_total, ing.unidad, insumo_ing.unidad)

            MovimientoInventario.objects.create(
                insumo=insumo_ing,
                cantidad=cant_norm,
                tipo="salida",
                unidad=insumo_ing.unidad,
                pizzeria=lote.pizzeria,
                usuario=lote.usuario,
                motivo=f"Consumo para lote #{lote.id} de {insumo_obj.nombre}",
            )

        # 4) Entrada del insumo objetivo con el rendimiento real capturado
        MovimientoInventario.objects.create(
            insumo=insumo_obj,
            cantidad=rendimiento,
            tipo="entrada",
            unidad=insumo_obj.unidad,
            pizzeria=lote.pizzeria,
            usuario=lote.usuario,
            motivo=f"Producción lote #{lote.id} (rendimiento real)",
        )

        lote.rendimiento_real = rendimiento
        lote.confirmado = True
        lote.save()
