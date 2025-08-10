# productos/admin.py
from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "pizzeria", "precio", "activo", "created_at")
    list_filter = ("pizzeria", "activo", "categoria")
    search_fields = ("nombre",)
