# ventas/urls.py

from django.urls import path
from .views import (
    current_user,
    PizzeriaListCreateAPIView,
    PizzeriaRetrieveUpdateDestroyAPIView,
    VentaListCreateAPIView,
    VentaRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    # GET /api/user/  -> devuelve user id, username y email
    path("user/", current_user, name="current-user"),

    # Pizzerías CRUD
    path("pizzerias/", PizzeriaListCreateAPIView.as_view(), name="lista-pizzerias"),
    path(
        "pizzerias/<int:pizzeria_id>/",
        PizzeriaRetrieveUpdateDestroyAPIView.as_view(),
        name="detalle-pizzeria",
    ),

    # Ventas CRUD anidado: lista y crea
    path(
        "pizzerias/<int:pizzeria_id>/ventas/",
        VentaListCreateAPIView.as_view(),
        name="ventas-list-create",
    ),

    # Ventas CRUD directo: detalle, actualiza y elimina
    path(
        "ventas/<int:venta_id>/",
        VentaRetrieveUpdateDestroyAPIView.as_view(),
        name="venta-detalle",
    ),
]
