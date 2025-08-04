from django.urls import path
from ventas.views import (
    # Pizzerías
    PizzeriaListCreateAPIView,
    PizzeriaRetrieveUpdateDestroyAPIView,

    # Ventas
    VentaListCreateAPIView,
    VentaRetrieveUpdateDestroyByPizzeriaAPIView,
    VentaRetrieveAPIView,

    # Productos
    ProductoListCreateByPizzeriaAPIView,
    resumen_ventas,
    ProductoRetrieveUpdateDestroyByPizzeriaAPIView,

    # Etapas
    VentaEtapaCreateAPIView,
    VentaEtapaListAPIView,
    VentaEtapaDuracionesAPIView,
    VentaEtapaActualAPIView,

    # Estadísticas
    resumen_ventas,
    ventas_por_dia,
    ventas_ayer,
)

urlpatterns = [
    # ——————————————————————————————————————————
    # CRUD Pizzerías
    # ——————————————————————————————————————————
    path("pizzerias/", PizzeriaListCreateAPIView.as_view(), name="lista-pizzerias"),
    path("pizzerias/<int:pizzeria_id>/", PizzeriaRetrieveUpdateDestroyAPIView.as_view(), name="detalle-pizzeria"),

    # ——————————————————————————————————————————
    # CRUD Ventas (por pizzería)
    # ——————————————————————————————————————————
    path("pizzerias/<int:pizzeria_id>/ventas/", VentaListCreateAPIView.as_view(), name="ventas-list-create"),
    path("pizzerias/<int:pizzeria_id>/ventas/<int:venta_id>/", VentaRetrieveUpdateDestroyByPizzeriaAPIView.as_view(), name="venta-detail-by-pizzeria"),
    path("ventas/<int:pk>/", VentaRetrieveAPIView.as_view(), name="venta-detalle"),

    # ——————————————————————————————————————————
    # CRUD Productos (por pizzería)
    # ——————————————————————————————————————————
    path("pizzerias/<int:pizzeria_id>/productos/", ProductoListCreateByPizzeriaAPIView.as_view(), name="productos-por-pizzeria"),
    path("pizzerias/<int:pizzeria_id>/productos/<int:pk>/", ProductoRetrieveUpdateDestroyByPizzeriaAPIView.as_view(), name="producto-detail-by-pizzeria"),

    # ——————————————————————————————————————————
    # Etapas de Venta
    # ——————————————————————————————————————————
    path("ventas/etapas/", VentaEtapaCreateAPIView.as_view(), name="registrar-etapa-venta"),
    path("ventas/<int:venta_id>/etapas/", VentaEtapaListAPIView.as_view(), name="listar-etapas-venta"),
    path("ventas/<int:venta_id>/etapas/tiempos/", VentaEtapaDuracionesAPIView.as_view(), name="tiempos-entre-etapas"),
    path("ventas/<int:venta_id>/estado/", VentaEtapaActualAPIView.as_view(), name="estado-venta"),

    # ——————————————————————————————————————————
    # Estadísticas y Resúmenes de Ventas
    # ——————————————————————————————————————————
    path("ventas/resumen/", resumen_ventas, name="resumen-ventas"),
    path("ventas/por-dia/", ventas_por_dia, name="ventas-por-dia"),
    path("ventas/ayer/", ventas_ayer, name="ventas-ayer"),
]
