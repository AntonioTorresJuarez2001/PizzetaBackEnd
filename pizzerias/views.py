# pizzerias/views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from usuarios.permissions import EmpleadoSoloLecturaPermission
from pizzerias.models import Pizzeria
from .serializers import (
    PizzeriaSerializer
)
from drf_yasg.utils import swagger_auto_schema
from usuarios.models import DuenoPizzeria

class PizzeriaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, EmpleadoSoloLecturaPermission]
    serializer_class = PizzeriaSerializer

    @swagger_auto_schema(tags=["Unidades (Pizzerías)"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Unidades (Pizzerías)"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return Pizzeria.objects.filter(
            dueno_asignaciones__dueno=self.request.user
        ).annotate(total_ventas=Sum("ventas__total"))

    def perform_create(self, serializer):
        pizzeria = serializer.save()
        DuenoPizzeria.objects.create(dueno=self.request.user, pizzeria=pizzeria)

class PizzeriaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, EmpleadoSoloLecturaPermission]
    serializer_class = PizzeriaSerializer
    lookup_url_kwarg = "pizzeria_id"

    @swagger_auto_schema(tags=["Unidades (Pizzerías)"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Unidades (Pizzerías)"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(tags=["Unidades (Pizzerías)"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Unidades (Pizzerías)"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Pizzeria.objects.filter(dueno_asignaciones__dueno=self.request.user)
