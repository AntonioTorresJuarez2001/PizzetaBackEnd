from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Sum, ProtectedError
from .models import Pizzeria, Venta, DuenoPizzeria, Producto
from .serializers import (
    PizzeriaSerializer,
    VentaSerializer,
    ProductoSerializer
)

# ————————————————————————————————————————————————————————————————
# Utilidad para verificar si un usuario es dueño de una pizzería
# ————————————————————————————————————————————————————————————————
def check_dueno(user, pizzeria_id):
    if not DuenoPizzeria.objects.filter(dueno=user, pizzeria_id=pizzeria_id).exists():
        raise PermissionDenied("No tienes permiso para acceder a esta pizzería.")

# ————————————————————————————————————————————————————————————————
# 1) CRUD de Pizzerías
# ————————————————————————————————————————————————————————————————

class PizzeriaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PizzeriaSerializer

    def get_queryset(self):
        return Pizzeria.objects.filter(
            dueño_asignaciones__dueno=self.request.user
        ).annotate(total_ventas=Sum("ventas__total"))

    def perform_create(self, serializer):
        pizzeria = serializer.save()
        DuenoPizzeria.objects.create(
            dueno=self.request.user,
            pizzeria=pizzeria
        )


class PizzeriaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PizzeriaSerializer
    lookup_url_kwarg = "pizzeria_id"

    def get_queryset(self):
        return Pizzeria.objects.filter(
            dueño_asignaciones__dueno=self.request.user
        )

# ————————————————————————————————————————————————————————————————
# 2) CRUD de Ventas
# ————————————————————————————————————————————————————————————————

class VentaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VentaSerializer

    def get_queryset(self):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        return Venta.objects.filter(pizzeria_id=pizzeria_id).order_by("-fecha")

    def perform_create(self, serializer):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        serializer.save(pizzeria_id=pizzeria_id, dueno=self.request.user)


class VentaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VentaSerializer
    lookup_url_kwarg = "venta_id"

    def get_queryset(self):
        return Venta.objects.filter(
            pizzeria__dueño_asignaciones__dueno=self.request.user
        )


class VentaRetrieveUpdateDestroyByPizzeriaAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VentaSerializer
    lookup_url_kwarg = "venta_id"

    def get_queryset(self):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        return Venta.objects.filter(pizzeria_id=pizzeria_id)

    def perform_update(self, serializer):
        pizzeria_id = self.kwargs["pizzeria_id"]
        serializer.save(pizzeria_id=pizzeria_id, dueno=self.request.user)

    def destroy(self, request, *args, **kwargs):
        venta = self.get_object()
        try:
            venta.delete()
        except ProtectedError:
            return Response(
                {"detail": "No puedes eliminar una venta que ya tiene items relacionados."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

# ————————————————————————————————————————————————————————————————
# 3) CRUD de Productos (anidados por pizzería)
# ————————————————————————————————————————————————————————————————

class ProductoListCreateByPizzeriaAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductoSerializer

    def get_queryset(self):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        return Producto.objects.filter(pizzeria_id=pizzeria_id)

    def perform_create(self, serializer):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        serializer.save(pizzeria_id=pizzeria_id)


class ProductoRetrieveUpdateDestroyByPizzeriaAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductoSerializer
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        return Producto.objects.filter(pizzeria_id=pizzeria_id)

    def destroy(self, request, *args, **kwargs):
        producto = self.get_object()
        try:
            producto.delete()
        except ProtectedError:
            return Response(
                {"detail": "No puedes eliminar un producto que ya ha sido vendido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

# ————————————————————————————————————————————————————————————————
# 4) Endpoint para obtener el usuario autenticado
# ————————————————————————————————————————————————————————————————

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    u = request.user
    return Response({
        "id": u.id,
        "username": u.username,
        "email": u.email
    })
