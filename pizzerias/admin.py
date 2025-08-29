from django.contrib import admin
from .models import Pizzeria

@admin.register(Pizzeria)
class PizzeriaAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "telefono", "created_at"]
    search_fields = ["nombre", "direccion"]
