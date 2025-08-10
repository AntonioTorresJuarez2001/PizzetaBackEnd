from django.urls import path
from productos.views import (
    
    # Productos
    ProductoListCreateByPizzeriaAPIView,
    ProductoRetrieveUpdateDestroyByPizzeriaAPIView,
    ImportProductosAPIView
    
)

urlpatterns = [
    
    # ——————————————————————————————————————————
    # CRUD Productos (por pizzería)
    # ——————————————————————————————————————————
    path("pizzerias/<int:pizzeria_id>/productos/", ProductoListCreateByPizzeriaAPIView.as_view(), name="productos-por-pizzeria"),
    path("pizzerias/<int:pizzeria_id>/productos/<int:pk>/", ProductoRetrieveUpdateDestroyByPizzeriaAPIView.as_view(), name="producto-detail-by-pizzeria"),

    path("pizzerias/<int:pizzeria_id>/productos/importar/", ImportProductosAPIView.as_view(), name="productos-importar"),

    ]
