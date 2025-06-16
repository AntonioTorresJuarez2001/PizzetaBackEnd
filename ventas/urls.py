from django.urls import path
from .views import (
    current_user,
    PizzeriaListCreateAPIView,
    PizzeriaRetrieveUpdateDestroyAPIView,
    VentaListCreateAPIView,
    VentaRetrieveUpdateDestroyByPizzeriaAPIView,  # Usamos solo esta
    ProductoListCreateByPizzeriaAPIView,
    ProductoRetrieveUpdateDestroyByPizzeriaAPIView,
)

urlpatterns = [
    path("user/", current_user, name="current-user"),

    # Pizzerías
    path("pizzerias/", PizzeriaListCreateAPIView.as_view(), name="lista-pizzerias"),
    path("pizzerias/<int:pizzeria_id>/", PizzeriaRetrieveUpdateDestroyAPIView.as_view(), name="detalle-pizzeria"),

    # Ventas (100% anidadas)
    path("pizzerias/<int:pizzeria_id>/ventas/", VentaListCreateAPIView.as_view(), name="ventas-list-create"),
    path("pizzerias/<int:pizzeria_id>/ventas/<int:venta_id>/", VentaRetrieveUpdateDestroyByPizzeriaAPIView.as_view(), name="venta-detail-by-pizzeria"),

    # Productos ANIDADOS
    path("pizzerias/<int:pizzeria_id>/productos/", ProductoListCreateByPizzeriaAPIView.as_view(), name="productos-por-pizzeria"),
    path("pizzerias/<int:pizzeria_id>/productos/<int:pk>/", ProductoRetrieveUpdateDestroyByPizzeriaAPIView.as_view(), name="producto-detail-by-pizzeria"),
]
