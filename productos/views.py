from rest_framework import generics
from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from .serializers import ProductoSerializer
from usuarios.permissions import EmpleadoSoloLecturaPermission
from rest_framework.permissions import IsAuthenticated
from usuarios.utils.roles import check_dueno
from django.db.models import ProtectedError
from productos.models import Producto


# ————————————————————————————————————————————————————————————————
# 3) CRUD de Productos (anidados por pizzería)
# ————————————————————————————————————————————————————————————————

class ProductoListCreateByPizzeriaAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, EmpleadoSoloLecturaPermission]
    serializer_class = ProductoSerializer

    @swagger_auto_schema(tags=["Productos"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Productos"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        return Producto.objects.filter(pizzeria_id=pizzeria_id)

    def perform_create(self, serializer):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        serializer.save(pizzeria_id=pizzeria_id)



class ProductoRetrieveUpdateDestroyByPizzeriaAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, EmpleadoSoloLecturaPermission]
    serializer_class = ProductoSerializer
    lookup_url_kwarg = "pk"  # coincide con tu URL

    # Swagger: etiqueta las operaciones
    @swagger_auto_schema(tags=["Productos"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Productos"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(tags=["Productos"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Productos"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        # 1) Cuando drf-yasg genera el esquema, no hay kwargs -> corta y evita side-effects
        if getattr(self, "swagger_fake_view", False):
            return Producto.objects.none()

        # 2) Evita KeyError si por alguna razón no viene la ruta completa
        pizzeria_id = self.kwargs.get("pizzeria_id")
        if not pizzeria_id:
            return Producto.objects.none()

        # 3) Revisa permisos ya en contexto real (no durante schema)
        check_dueno(self.request.user, pizzeria_id)

        return Producto.objects.filter(pizzeria_id=pizzeria_id)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            # DRF espera que lances una excepción o manejes la respuesta en destroy();
            # aquí levantamos una ValidationError para que DRF responda 400.
            from rest_framework.exceptions import ValidationError
            raise ValidationError("No puedes eliminar un producto que ya ha sido vendido.")
