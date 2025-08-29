from django.urls import path
from .views import (
    # Pizzerías
    PizzeriaListCreateAPIView,
    PizzeriaRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    # ——————————————————————————————————————————
    # CRUD Pizzerías
    # ——————————————————————————————————————————
    path("pizzerias/", PizzeriaListCreateAPIView.as_view(), name="lista-pizzerias"),
    path("pizzerias/<int:pizzeria_id>/", PizzeriaRetrieveUpdateDestroyAPIView.as_view(), name="detalle-pizzeria"),


]
