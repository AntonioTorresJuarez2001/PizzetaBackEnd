# ventas/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from .models import Pizzeria, Venta, DuenoPizzeria
from .serializers import PizzeriaSerializer, VentaSerializer





# ————————————————————————————————————————————————————————————————
# 1) CRUD de Pizzerías
# ————————————————————————————————————————————————————————————————

class PizzeriaListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/pizzerias/  -> Lista las pizzerías donde el usuario es dueño, 
                             con un campo extra `total_ventas`.
    POST /api/pizzerias/  -> Crea una nueva pizzería y asigna al usuario como dueño.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PizzeriaSerializer

    def get_queryset(self):
        # Filtramos sólo las pizzerías donde el usuario es dueño...
        qs = Pizzeria.objects.filter(dueño_asignaciones__dueno=self.request.user)
        # ...y anotamos en cada objeto el total sumado de sus ventas:
        qs = qs.annotate(total_ventas=Sum("ventas__total"))
        return qs
    
    def perform_create(self, serializer):
    # Guardamos primero la pizzería
        pizzeria = serializer.save()
    
    # Luego la asociamos al usuario actual como dueño
        DuenoPizzeria.objects.create(
            dueno=self.request.user,
            pizzeria=pizzeria
        )


class PizzeriaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/pizzerias/{pizzeria_id}/    -> Recupera detalle de la pizzería (sólo si es dueño).
    PUT    /api/pizzerias/{pizzeria_id}/    -> Actualiza la pizzería (sólo si es dueño).
    PATCH  /api/pizzerias/{pizzeria_id}/    -> Actualiza parcialmente (sólo si es dueño).
    DELETE /api/pizzerias/{pizzeria_id}/    -> Elimina la pizzería (sólo si es dueño).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PizzeriaSerializer
    lookup_url_kwarg = "pizzeria_id"

    def get_queryset(self):
        # Sólo pizzerías donde el usuario autenticado es dueño
        return Pizzeria.objects.filter(dueño_asignaciones__dueno=self.request.user)


# ————————————————————————————————————————————————————————————————
# 2) CRUD de Ventas
# ————————————————————————————————————————————————————————————————

class VentaListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/pizzerias/{pizzeria_id}/ventas/   -> Lista ventas de esa pizzería (si es dueño).
    POST /api/pizzerias/{pizzeria_id}/ventas/   -> Crea nueva venta para la pizzería con dueno=request.user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VentaSerializer

    def get_queryset(self):
        pizzeria_id = self.kwargs["pizzeria_id"]
        # Validar que el usuario sea dueño de esa pizzería
        DuenoPizzeria.objects.get(dueno=self.request.user, pizzeria_id=pizzeria_id)
        return Venta.objects.filter(pizzeria_id=pizzeria_id).order_by("-fecha")

    def perform_create(self, serializer):
        pizzeria_id = self.kwargs["pizzeria_id"]
        # Validar nuevamente dueño antes de crear
        DuenoPizzeria.objects.get(dueno=self.request.user, pizzeria_id=pizzeria_id)
        serializer.save(pizzeria_id=pizzeria_id, dueno=self.request.user)


class VentaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/ventas/{venta_id}/   -> Recupera detalle de la venta (si pertenece a pizzería del dueño).
    PUT    /api/ventas/{venta_id}/   -> Actualiza la venta (si el dueño es el mismo).
    PATCH  /api/ventas/{venta_id}/   -> Actualiza parcialmente.
    DELETE /api/ventas/{venta_id}/   -> Elimina la venta (si el dueño es el mismo).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VentaSerializer
    lookup_url_kwarg = "venta_id"

    def get_queryset(self):
        # Sólo ventas asociadas a pizzerías donde request.user sea dueño
        return Venta.objects.filter(
            pizzeria__dueño_asignaciones__dueno=self.request.user
        )


# ————————————————————————————————————————————————————————————————
# 3) Función current_user (opcional, si React la usa)
# ————————————————————————————————————————————————————————————————

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Devuelve información mínima del usuario autenticado:
      { "id": ..., "username": "...", "email": "..." }
    """
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
    })
