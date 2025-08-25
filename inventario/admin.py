from django.contrib import admin
from .models import Insumo, MovimientoInventario, Receta, Ingrediente, SalidaAutomaticaVenta, FormulaInsumo, FormulaIngrediente, LoteProduccion

# ---------- INSUMO ----------
@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "pizzeria", "unidad", "stock_minimo", "stock_actual", "activo", "fecha_creacion")
    list_filter  = ("pizzeria", "unidad", "activo")
    search_fields = ("nombre", "pizzeria__nombre")
    ordering = ("pizzeria", "nombre")
    readonly_fields = ("stock_actual", "fecha_creacion")

    actions = ["marcar_activos", "marcar_inactivos"]

    @admin.action(description="Marcar como activos")
    def marcar_activos(self, request, queryset):
        queryset.update(activo=True)

    @admin.action(description="Marcar como inactivos")
    def marcar_inactivos(self, request, queryset):
        queryset.update(activo=False)

# ---------- MOVIMIENTOS ----------
@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "pizzeria", "insumo", "tipo", "cantidad", "unidad", "usuario", "motivo")
    list_filter  = ("pizzeria", "tipo", "unidad", "fecha")
    search_fields = ("insumo__nombre", "usuario__username", "motivo")
    date_hierarchy = "fecha"
    ordering = ("-fecha",)
    autocomplete_fields = ("pizzeria", "insumo", "usuario")
    readonly_fields = ("fecha",)

    # (Opcional) Evitar ediciones después de crear:
    # def has_change_permission(self, request, obj=None):
    #     return False

# ---------- RECETAS + INGREDIENTES ----------
class IngredienteInline(admin.TabularInline):
    model = Ingrediente
    extra = 0
    autocomplete_fields = ("insumo",)
    fields = ("insumo", "cantidad", "unidad")
    # Evita ruido si tu `Ingrediente` ya normaliza unidades por `Insumo`
    # readonly_fields = ("unidad",)

@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ("producto", "activa", "fecha_creacion")
    list_filter  = ("activa", "producto__pizzeria")
    search_fields = ("producto__nombre",)
    ordering = ("-fecha_creacion",)
    inlines = [IngredienteInline]

# ---------- TRAZA DE SALIDAS POR VENTA ----------
@admin.register(SalidaAutomaticaVenta)
class SalidaAutomaticaVentaAdmin(admin.ModelAdmin):
    list_display = ("venta", "insumo", "cantidad", "unidad")
    list_filter  = ("insumo__pizzeria",)
    search_fields = ("venta__id", "insumo__nombre")
    ordering = ("-id",)
    autocomplete_fields = ("venta", "insumo")

class FormulaIngredienteInline(admin.TabularInline):
    model = FormulaIngrediente
    extra = 0
    autocomplete_fields = ("insumo",)
    fields = ("insumo", "cantidad", "unidad")

@admin.register(FormulaInsumo)
class FormulaInsumoAdmin(admin.ModelAdmin):
    list_display = ("insumo_objetivo", "activa", "factor_rendimiento_esperado", "fecha_creacion")
    list_filter  = ("activa", "insumo_objetivo__pizzeria")
    search_fields = ("insumo_objetivo__nombre",)
    ordering = ("-fecha_creacion",)
    inlines = [FormulaIngredienteInline]

@admin.register(LoteProduccion)
class LoteProduccionAdmin(admin.ModelAdmin):
    list_display = ("id", "formula", "pizzeria", "cantidad_objetivo", "unidad_objetivo",
                    "rendimiento_real", "confirmado", "fecha")
    list_filter  = ("confirmado", "pizzeria")
    autocomplete_fields = ("formula", "usuario", "pizzeria")
    readonly_fields = ("fecha",)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # si hay fórmula seleccionada, proponemos automáticamente la unidad del insumo objetivo
        if obj and obj.formula:
            form.base_fields["unidad_objetivo"].initial = obj.formula.insumo_objetivo.unidad
        return form
