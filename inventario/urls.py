from django.urls import path
from .views import (
    InsumoListCreateView,
    InsumoDetailView,
    MovimientoInventarioListCreateView,
    RecetaListView,
    RecetaDetailView,
    RecetaCreateView,
)

urlpatterns = [
    # Insumos
    path("insumos/", InsumoListCreateView.as_view(), name="insumo-list-create"),
    path("insumos/<int:pk>/", InsumoDetailView.as_view(), name="insumo-detail"),

    # Movimientos
    path("movimientos/", MovimientoInventarioListCreateView.as_view(), name="movimiento-list-create"),

    # Recetas
    path("recetas/", RecetaListView.as_view(), name="receta-list"),
    path("recetas/<int:pk>/", RecetaDetailView.as_view(), name="receta-detail"),
    path("recetas/crear/", RecetaCreateView.as_view(), name="receta-crear"),
]
