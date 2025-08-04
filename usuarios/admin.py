from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from usuarios.models import DuenoPizzeria, UserProfile

# Mostrar perfil (rol) en admin de usuario
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fk_name = 'user'

class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

    def rol(self, obj):
        return obj.perfil.rol if hasattr(obj, 'perfil') else "-"
    rol.short_description = 'Rol'

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'rol')
    list_select_related = ('perfil',)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Admin de UserProfile separado (opcional)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "rol")
    list_filter = ("rol",)
    search_fields = ("user__username",)

# Admin de DuenoPizzeria
@admin.register(DuenoPizzeria)
class DuenoPizzeriaAdmin(admin.ModelAdmin):
    list_display = ("id", "dueno", "pizzeria", "created_at")
    list_filter = ("dueno", "pizzeria")
