from django.contrib import admin
from .models import Insumo, MovimientoInventario, Receta, Ingrediente, SalidaAutomaticaVenta

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
