from django.contrib import admin
from .models import Pizzeria, Venta

@admin.register(Pizzeria)
class PizzeriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "direccion", "telefono")
    search_fields = ("nombre",)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "pizzeria", "dueno", "fecha", "total", "metodo_pago")
    list_filter = ("pizzeria", "dueno", "metodo_pago")
    date_hierarchy = "fecha"
