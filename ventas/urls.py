from django.urls import path
from .views import (
    current_user,
    PizzeriaListCreateAPIView,
    PizzeriaRetrieveUpdateDestroyAPIView,
    VentaListCreateAPIView,
    VentaRetrieveUpdateDestroyByPizzeriaAPIView,
    ProductoListCreateByPizzeriaAPIView,
    resumen_ventas,
    ProductoRetrieveUpdateDestroyByPizzeriaAPIView,
    VentaEtapaCreateAPIView,
    VentaEtapaListAPIView,
    VentaEtapaDuracionesAPIView,
    VentaEtapaActualAPIView,
    ventas_por_dia,
    ventas_ayer,
    UsuarioPizzeriaRolListCreateAPIView,
    UsuarioPizzeriaRolRetrieveUpdateDestroyAPIView,
    CrearEmpleadoAPIView,
    EmpleadosDelDuenoAPIView,
    EstablecerPinPlanoAPIView,
    ConsultarPinPlanoAPIView,
    verificar_pin_plano
    )

urlpatterns = [
    # Usuarios y resumen
    path("ventas/resumen/", resumen_ventas, name="resumen-ventas"),
    path("ventas-por-dia/", ventas_por_dia, name="ventas-por-dia"),  # Nueva ruta
    path("ventas/ayer/", ventas_ayer, name="ventas-ayer"),  # Nueva ruta para ayer
    path("user/", current_user, name="current-user"),
    path("usuarios_pizzeria/", UsuarioPizzeriaRolListCreateAPIView.as_view(), name="lista-crea-roles"),
    path("usuarios_pizzeria/<int:rol_id>/", UsuarioPizzeriaRolRetrieveUpdateDestroyAPIView.as_view(), name="rol-detalle"),


    # Pizzerías
    path("pizzerias/", PizzeriaListCreateAPIView.as_view(), name="lista-pizzerias"),
    path("pizzerias/<int:pizzeria_id>/", PizzeriaRetrieveUpdateDestroyAPIView.as_view(), name="detalle-pizzeria"),

    # Ventas (anidadas)
    path("pizzerias/<int:pizzeria_id>/ventas/", VentaListCreateAPIView.as_view(), name="ventas-list-create"),
    path("pizzerias/<int:pizzeria_id>/ventas/<int:venta_id>/", VentaRetrieveUpdateDestroyByPizzeriaAPIView.as_view(), name="venta-detail-by-pizzeria"),

    # Productos anidados
    path("pizzerias/<int:pizzeria_id>/productos/", ProductoListCreateByPizzeriaAPIView.as_view(), name="productos-por-pizzeria"),
    path("pizzerias/<int:pizzeria_id>/productos/<int:pk>/", ProductoRetrieveUpdateDestroyByPizzeriaAPIView.as_view(), name="producto-detail-by-pizzeria"),

    # Etapas de venta
    path("ventas/etapas/", VentaEtapaCreateAPIView.as_view(), name="registrar-etapa-venta"),
    path("ventas/<int:venta_id>/etapas/", VentaEtapaListAPIView.as_view(), name="listar-etapas-venta"),
    path("ventas/<int:venta_id>/etapas/tiempos/", VentaEtapaDuracionesAPIView.as_view(), name="tiempos-entre-etapas"),
    path("ventas/<int:venta_id>/estado/", VentaEtapaActualAPIView.as_view(), name="estado-venta"),
    
    path("empleados/", CrearEmpleadoAPIView.as_view(), name="crear-empleado"),
    path("mis-empleados/", EmpleadosDelDuenoAPIView.as_view(), name="mis-empleados"),
    
    #Pin
    path("pin/plano/establecer/", EstablecerPinPlanoAPIView.as_view(), name="establecer-pin-plano"),
    path("pin/plano/consultar/", ConsultarPinPlanoAPIView.as_view(), name="consultar-pin-plano"),
    path("pin/plano/verificar/", verificar_pin_plano),

]
