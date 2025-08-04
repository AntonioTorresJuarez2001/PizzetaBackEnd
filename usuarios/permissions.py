# usuarios/permissions.py

from rest_framework import permissions
from usuarios.utils.roles import get_rol_en_pizzeria


class EmpleadoSoloLecturaPermission(permissions.BasePermission):
    """
    Empleados solo pueden leer. Dueños, gerentes, etc. pueden escribir.
    Si no hay pizzeria_id, se permite el POST (ej: crear nueva pizzería).
    """

    def has_permission(self, request, view):
        # Permitir siempre lectura
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Si es POST y no se requiere pizzeria_id, dejar pasar
        if request.method == "POST" and "pizzeria_id" not in view.kwargs:
            return True

        # Para PUT, PATCH, DELETE — verificar el rol en la pizzería
        pizzeria_id = view.kwargs.get("pizzeria_id")
        if not pizzeria_id:
            return False

        rol = get_rol_en_pizzeria(request.user, pizzeria_id)
        return rol != "empleado"
