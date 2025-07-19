# ventas/utils/roles.py

from ..models import UsuarioPizzeriaRol, DuenoPizzeria
from rest_framework.exceptions import PermissionDenied


def get_rol_en_pizzeria(user, pizzeria_id):
    """
    Retorna el rol del usuario en una pizzería específica.
    Si no tiene rol asignado, retorna None.
    """
    try:
        asignacion = UsuarioPizzeriaRol.objects.get(user=user, pizzeria_id=pizzeria_id)
        return asignacion.rol
    except UsuarioPizzeriaRol.DoesNotExist:
        return None

