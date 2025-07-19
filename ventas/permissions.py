# ventas/permissions.py

from rest_framework import permissions
from ventas.utils.roles import get_rol_en_pizzeria

class EmpleadoSoloLecturaPermission(permissions.BasePermission):
    """
    Permite solo métodos de lectura (GET, HEAD, OPTIONS) si el usuario tiene
    rol 'empleado' en la pizzería correspondiente.
    Para otros roles, se permite acceso completo.
    """

def has_permission(self, request, view):
    # Si es un método de lectura, lo permitimos siempre que esté autenticado
    if request.method in permissions.SAFE_METHODS:
        return request.user.is_authenticated

    # Para POST, PUT, DELETE, intentamos verificar rol con pizzeria_id si está disponible
    pizzeria_id = view.kwargs.get("pizzeria_id")
    if not pizzeria_id:
        return False  # No se puede verificar permiso de escritura

    rol = get_rol_en_pizzeria(request.user, pizzeria_id)
    return rol != "empleado"  # Solo empleados tienen acceso limitado
