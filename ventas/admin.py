from django.contrib import admin
from .models import Pizzeria, Venta

@admin.register(Pizzeria)
class PizzeriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "direccion", "telefono")
    search_fields = ("nombre",)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    search_fields = ("id",)
    list_display = ("id", "pizzeria", "dueno", "fecha", "total", "metodo_pago")
    list_filter = ("pizzeria", "dueno", "metodo_pago")
    date_hierarchy = "fecha"
    autocomplete_fields = ("pizzeria", "dueno")
    search_fields = ("id", "pizzeria__nombre", "dueno__username")

