from rest_framework import permissions

class SoloLecturaPermission(permissions.BasePermission):
    """
    Permite solo métodos de lectura (GET, HEAD, OPTIONS) si el usuario tiene rol 'solo_lectura'.
    Para todos los demás roles, se permite acceso completo.
    """

    def has_permission(self, request, view):
        perfil = getattr(request.user, "perfil", None)

        if perfil and perfil.rol == "solo_lectura":
            return request.method in permissions.SAFE_METHODS  # solo GET, HEAD, OPTIONS

        return True  # admin o normal pueden hacer todo
