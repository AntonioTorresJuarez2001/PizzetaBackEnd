from django.urls import path
from .views import current_user, ListaPizzeriasUsuario, ListaVentasPorPizzeria
# (asegúrate de que ya estén importados tus otros views)

urlpatterns = [
    path('user/', current_user, name='current-user'),

    
    path("pizzerias/", ListaPizzeriasUsuario.as_view(), name="lista-pizzerias"),
    path("pizzerias/<int:pizzeria_id>/ventas/", ListaVentasPorPizzeria.as_view(), name="ventas-por-pizzeria"),
]



