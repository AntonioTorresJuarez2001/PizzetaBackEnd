# usuarios/utils/roles.py
from ..models import UsuarioPizzeriaRol, DuenoPizzeria
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import PermissionDenied
from usuarios.models import DuenoPizzeria

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

def check_dueno(user, pizzeria_id):
    """
    Verifica que el usuario sea dueño de la pizzería indicada.
    Lanza excepción 403 si no lo es.
    """
    if not DuenoPizzeria.objects.filter(dueno=user, pizzeria_id=pizzeria_id).exists():
        raise PermissionDenied("No tiene permisos sobre esta pizzería.")
