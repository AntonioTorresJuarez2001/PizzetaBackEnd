# ventas/admin.py

from django.contrib import admin
from django.contrib.auth.models import User  # No lo registraremos, solo lo usamos en FK
from django.contrib.auth.admin import UserAdmin  # Si necesitas personalizar User, lo haces en otro lugar
from .models import Pizzeria, DuenoPizzeria, Venta

# —————— ELIMINAMOS cualquier @admin.register(User) para evitar duplicados ——————

@admin.register(Pizzeria)
class PizzeriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "direccion", "telefono")
    search_fields = ("nombre",)

@admin.register(DuenoPizzeria)
class DuenoPizzeriaAdmin(admin.ModelAdmin):
    list_display = ("id", "dueno", "pizzeria", "created_at")
    list_filter = ("dueno", "pizzeria")

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "pizzeria", "dueno", "fecha", "total", "metodo_pago")
    list_filter = ("pizzeria", "dueno", "metodo_pago")
    date_hierarchy = "fecha"
