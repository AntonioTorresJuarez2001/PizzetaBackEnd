# usuarios/models.py

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password, check_password
from pizzerias.models import Pizzeria

# Create your models here.
class DuenoPizzeria(models.Model):
    dueno      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="dueno_id",
        related_name="pizzeria_asignaciones"
    )
    pizzeria   = models.ForeignKey(
        Pizzeria,
        on_delete=models.CASCADE,
        db_column="pizzeria_id",
        related_name="dueno_asignaciones"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dueno_pizzeria"
        unique_together = ("dueno", "pizzeria")
        verbose_name = "Asignación Dueño-Pizzería"
        verbose_name_plural = "Asignaciones Dueño-Pizzería"

    def __str__(self):
        return f"{self.dueno.username} → {self.pizzeria.nombre}"

class UsuarioPizzeriaRol(models.Model):
    ROLES = [
        ("dueno", "Dueño"),
        ("gerente", "Gerente"),
        ("subgerente", "Subgerente"),
        ("cajero", "Cajero"),
        ("empleado", "Empleado"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roles_por_pizzeria"
    )
    pizzeria = models.ForeignKey(
        Pizzeria,
        on_delete=models.CASCADE,
        related_name="usuarios_con_rol"
    )
    rol = models.CharField(max_length=20, choices=ROLES)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "usuario_pizzeria_rol"
        unique_together = ("user", "pizzeria")  # Un solo rol por pizzería
        verbose_name = "Rol de usuario en pizzería"
        verbose_name_plural = "Roles de usuarios en pizzerías"

    def __str__(self):
        return f"{self.user.username} - {self.pizzeria.nombre} → {self.rol}"

class UserProfile(models.Model):
    ROLES = [
        ("admin", "Administrador"),
        ("gerente", "Gerente"),
        ("subgerente", "Subgerente"),
        ("empleado", "Empleado"),
        ("dueno", "Dueño"),
        ("cajero", "Cajero"),
        ("solo_lectura", "Solo lectura"),
        ("sin_rol", "Sin Rol")
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    rol = models.CharField(max_length=30, choices=ROLES, default="empleado")  # o el que prefieras por defecto

    def __str__(self):
        return f"{self.user.username} - {self.rol}"

#pin
class TokenNumericoPlano(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="pin_plano")
    pin = models.CharField(max_length=6)  # PIN en texto plano
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PIN (PLANO) de {self.user.username}"
