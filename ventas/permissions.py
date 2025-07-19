from rest_framework import permissions

class SoloLecturaPermission(permissions.BasePermission):
    """
    Permite solo métodos de lectura (GET, HEAD, OPTIONS) si el usuario tiene rol 'solo_lectura'.
    Para todos los demás roles definidos, se permite acceso completo.
    """

    def has_permission(self, request, view):
        perfil = getattr(request.user, "perfil", None)

        if perfil:
            if perfil.rol == "solo_lectura":
                return request.method in permissions.SAFE_METHODS
            # Puedes agregar validaciones personalizadas por rol aquí si deseas
            return True

        return False  # No tiene perfil, denegar acceso
