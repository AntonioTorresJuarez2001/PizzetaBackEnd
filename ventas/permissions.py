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
        # Intentar obtener el ID de la pizzería desde la URL
        pizzeria_id = view.kwargs.get("pizzeria_id")

        # Si no hay pizzería en la URL, denegamos por seguridad
        if not pizzeria_id:
            return False

        rol = get_rol_en_pizzeria(request.user, pizzeria_id)

        if rol == "empleado":
            return request.method in permissions.SAFE_METHODS  # solo GET, HEAD, OPTIONS

        return True  # gerente, dueño, etc. tienen acceso total
