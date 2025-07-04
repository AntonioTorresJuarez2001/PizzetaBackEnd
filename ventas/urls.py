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
)

urlpatterns = [
    # Usuarios y resumen
    path("ventas/resumen/", resumen_ventas, name="resumen-ventas"),
    path("user/", current_user, name="current-user"),

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
]
