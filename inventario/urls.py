from django.urls import path
from .views import (
    InsumoListCreateView,
    InsumoDetailView,
    MovimientoInventarioListCreateView,
    RecetaListView,
    RecetaDetailView,
    RecetaCreateView,
    FormulaInsumoListCreateView, 
    FormulaInsumoDetailView,
    LoteProduccionCreateView, 
    LoteProduccionConfirmView
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
    
    path("formulas-insumo/", FormulaInsumoListCreateView.as_view(), name="formula-insumo-list-create"),
    path("formulas-insumo/<int:pk>/", FormulaInsumoDetailView.as_view(), name="formula-insumo-detail"),
    path("lotes/", LoteProduccionCreateView.as_view(), name="lote-produccion-create"),
    path("lotes/<int:pk>/confirmar/", LoteProduccionConfirmView.as_view(), name="lote-produccion-confirm"),

]
