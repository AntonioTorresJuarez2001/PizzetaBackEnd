from django.urls import path
from ventas.views import (
    
    # Ventas
    VentaListCreateAPIView,
    VentaRetrieveUpdateDestroyByPizzeriaAPIView,
    VentaRetrieveAPIView,
    resumen_ventas,


    # Etapas
    VentaEtapaCreateAPIView,
    VentaEtapaListAPIView,
    VentaEtapaDuracionesAPIView,
    VentaEtapaActualAPIView,

    # Estadísticas
    resumen_ventas,
    ventas_por_dia,
    ventas_ayer,
    
    FirebirdHctaordProxyAPIView,
    FirebirdImportVentaAPIView,
    CrearProductoDesdeFirebirdAPIView
    
)

urlpatterns = [
    
    # ——————————————————————————————————————————
    # CRUD Ventas (por pizzería)
    # ——————————————————————————————————————————
    path("pizzerias/<int:pizzeria_id>/ventas/", VentaListCreateAPIView.as_view(), name="ventas-list-create"),
    path("pizzerias/<int:pizzeria_id>/ventas/<int:venta_id>/", VentaRetrieveUpdateDestroyByPizzeriaAPIView.as_view(), name="venta-detail-by-pizzeria"),
    path("ventas/<int:pk>/", VentaRetrieveAPIView.as_view(), name="venta-detalle"),


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
    
    path("pizzerias/<int:pizzeria_id>/firebird/hctaord/", FirebirdHctaordProxyAPIView.as_view(), name="firebird-hctaord"),
    path("pizzerias/<int:pizzeria_id>/ventas/importar-firebird/",FirebirdImportVentaAPIView.as_view(),name="importar-venta-firebird"),
    path("pizzerias/<int:pizzeria_id>/productos/crear-desde-firebird/<int:id_pro>/",CrearProductoDesdeFirebirdAPIView.as_view(),name="crear-producto-desde-firebird"),
]
