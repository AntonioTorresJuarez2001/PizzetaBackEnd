from django.urls import path
from usuarios.views import (
    current_user,
    UsuarioPizzeriaRolListCreateAPIView,
    UsuarioPizzeriaRolRetrieveUpdateDestroyAPIView,
    CrearEmpleadoAPIView,
    EmpleadosDelDuenoAPIView,
    EstablecerPinPlanoAPIView,
    ConsultarPinPlanoAPIView,
    verificar_pin_plano,
)

urlpatterns = [
    # Info de usuario autenticado
    path("user/", current_user, name="current-user"),

    # Gestión de roles en pizzerías
    path("usuarios_pizzeria/", UsuarioPizzeriaRolListCreateAPIView.as_view(), name="lista-crea-roles"),
    path("usuarios_pizzeria/<int:rol_id>/", UsuarioPizzeriaRolRetrieveUpdateDestroyAPIView.as_view(), name="rol-detalle"),

    # Empleados
    path("empleados/", CrearEmpleadoAPIView.as_view(), name="crear-empleado"),
    path("mis-empleados/", EmpleadosDelDuenoAPIView.as_view(), name="mis-empleados"),

    # PIN
    path("pin/plano/establecer/", EstablecerPinPlanoAPIView.as_view(), name="establecer-pin-plano"),
    path("pin/plano/consultar/", ConsultarPinPlanoAPIView.as_view(), name="consultar-pin-plano"),
    path("pin/plano/verificar/", verificar_pin_plano),
]
