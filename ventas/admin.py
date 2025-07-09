# ventas/admin.py

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Pizzeria, DuenoPizzeria, Venta, UserProfile

# ----------------------------------------------
# Mostrar campos de perfil (rol) en User admin
# ----------------------------------------------
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

    # Opcional: para mostrar el campo rol en la lista de usuarios
    def rol(self, obj):
        return obj.perfil.rol if hasattr(obj, 'perfil') else "-"
    rol.short_description = 'Rol'

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'rol')
    list_select_related = ('perfil',)

# Re-registra el modelo User con el nuevo admin personalizado
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# ----------------------------------------------
# Otros modelos
# ----------------------------------------------
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

# (opcional) también lo puedes mantener visible aparte si quieres
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "rol")
    list_filter = ("rol",)
    search_fields = ("user__username",)
