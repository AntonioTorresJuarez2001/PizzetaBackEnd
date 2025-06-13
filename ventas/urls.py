# ventas/urls.py
from django.urls import path
from .views import (
    current_user,
    PizzeriaListCreateAPIView,
    PizzeriaRetrieveUpdateDestroyAPIView,
    VentaListCreateAPIView,
    VentaRetrieveUpdateDestroyAPIView,
    ProductoListCreateAPIView
)

urlpatterns = [
    path("user/", current_user, name="current-user"),
    path("pizzerias/", PizzeriaListCreateAPIView.as_view(), name="lista-pizzerias"),
    path("pizzerias/<int:pizzeria_id>/", PizzeriaRetrieveUpdateDestroyAPIView.as_view(), name="detalle-pizzeria"),
    path("pizzerias/<int:pizzeria_id>/ventas/", VentaListCreateAPIView.as_view(), name="ventas-list-create"),
    path("ventas/<int:venta_id>/", VentaRetrieveUpdateDestroyAPIView.as_view(), name="venta-detalle"),
    # al final de urlpatterns:
    path("productos/", ProductoListCreateAPIView.as_view(), name="productos-list-create"),

]
