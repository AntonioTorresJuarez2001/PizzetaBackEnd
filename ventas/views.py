# ventas/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Sum, ProtectedError
from datetime import datetime
from django.utils.timezone import now, timedelta
from .models import Pizzeria, Venta, DuenoPizzeria, Producto, VentaEtapa
from .serializers import (
    PizzeriaSerializer,
    VentaSerializer,
    ProductoSerializer,
    VentaEtapaSerializer
)


# ——————————————————————————————————————————
# Utilidad para validar dueño de pizzería
# ——————————————————————————————————————————
def check_dueno(user, pizzeria_id):
    if not DuenoPizzeria.objects.filter(dueno=user, pizzeria_id=pizzeria_id).exists():
        raise PermissionDenied("No tienes permiso para acceder a esta pizzería.")


# ——————————————————————————————————————————
# 0) Usuario autenticado
# ——————————————————————————————————————————
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    u = request.user
    return Response({
        "id": u.id,
        "username": u.username,
        "email": u.email
    })

# 1) CRUD Pizzerías
class PizzeriaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PizzeriaSerializer

    def get_queryset(self):
        return Pizzeria.objects.filter(
            dueno_asignaciones__dueno=self.request.user
        ).annotate(total_ventas=Sum("ventas__total"))

    def perform_create(self, serializer):
        pizzeria = serializer.save()
        DuenoPizzeria.objects.create(dueno=self.request.user, pizzeria=pizzeria)

class PizzeriaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PizzeriaSerializer
    lookup_url_kwarg = "pizzeria_id"

    def get_queryset(self):
        return Pizzeria.objects.filter(dueno_asignaciones__dueno=self.request.user)

# ------------------------------------------
# 2) CRUD Ventas
# ------------------------------------------
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
    
    def get_serializer_context(self):
        return {**super().get_serializer_context(), "permitir_vacia": True}
    
    def perform_create(self, serializer):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        venta = serializer.save(pizzeria_id=pizzeria_id, dueno=self.request.user)

        # Registrar automáticamente el inicio del pedido
        VentaEtapa.objects.create(
            venta=venta,
            etapa="toma_pedido_inicio",
            timestamp=now()
        )


class VentaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VentaSerializer
    lookup_url_kwarg = "venta_id"

    def get_queryset(self):
        return Venta.objects.filter(
            pizzeria__dueno_asignaciones__dueno=self.request.user
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


# ——————————————————————————————————————————
# 4) Resumen de Ventas
# ——————————————————————————————————————————
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resumen_ventas(request):
    user = request.user
    rango = request.query_params.get("rango", "total")
    inicio_str = request.query_params.get("inicio")
    fin_str = request.query_params.get("fin")

    hoy = now().date()
    inicio = None
    fin = hoy + timedelta(days=1)

    if rango == "hoy":
        inicio = hoy
    elif rango == "ayer":
        inicio = hoy - timedelta(days=1)
        fin = hoy
    elif rango == "semana":
        inicio = hoy - timedelta(days=7)
    elif rango == "personalizado" and inicio_str and fin_str:
        try:
            inicio = datetime.strptime(inicio_str, "%Y-%m-%d").date()
            fin = datetime.strptime(fin_str, "%Y-%m-%d").date() + timedelta(days=1)
        except ValueError:
            return Response({"error": "Fechas inválidas."}, status=400)

    ventas = Venta.objects.filter(pizzeria__dueno_asignaciones__dueno=user)
    if inicio:
        ventas = ventas.filter(fecha__date__gte=inicio, fecha__date__lt=fin)

    total = ventas.aggregate(total=Sum("total"))["total"] or 0

    return Response({
        "rango": rango,
        "total": float(total),
        "desde": str(inicio) if inicio else "todo",
        "hasta": str(fin) if inicio else "todo"
    })


# ——————————————————————————————————————————
# 5) Etapas de venta (registro, tiempos, estado actual)
# ——————————————————————————————————————————
class VentaEtapaCreateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VentaEtapaSerializer

    def perform_create(self, serializer):
        venta = serializer.validated_data["venta"]
        etapa = serializer.validated_data["etapa"]

        if venta.dueno != self.request.user:
            raise PermissionDenied("No puedes registrar eventos de una venta que no te pertenece.")

        if VentaEtapa.objects.filter(venta=venta, etapa=etapa).exists():
            raise ValidationError(f"Ya se registró la etapa '{etapa}' para esta venta.")

        # Validación por canal
        etapas_domicilio = {"envio_inicio", "regreso_repartidor"}
        if etapa in etapas_domicilio and venta.canal != "DOMICILIO":
            raise ValidationError(f"La etapa '{etapa}' solo aplica a ventas a domicilio.")

        serializer.save(timestamp=serializer.validated_data.get("timestamp", now()))


class VentaEtapaListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VentaEtapaSerializer

    def get_queryset(self):
        venta_id = self.kwargs["venta_id"]
        return VentaEtapa.objects.filter(venta_id=venta_id).order_by("timestamp")


class VentaEtapaDuracionesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, venta_id):
        etapas = VentaEtapa.objects.filter(venta_id=venta_id).order_by("timestamp")
        tiempos = []
        prev = None
        for etapa in etapas:
            if prev:
                diferencia = etapa.timestamp - prev.timestamp
                tiempos.append({
                    "de": prev.get_etapa_display(),
                    "a": etapa.get_etapa_display(),
                    "segundos": diferencia.total_seconds(),
                    "minutos": round(diferencia.total_seconds() / 60, 2),
                    "desde": prev.timestamp,
                    "hasta": etapa.timestamp,
                })
            prev = etapa

        duracion_total = (etapas.last().timestamp - etapas.first().timestamp).total_seconds() if etapas.count() >= 2 else 0

        return Response({
            "duraciones": tiempos,
            "total_segundos": duracion_total,
            "total_minutos": round(duracion_total / 60, 2)
        })


class VentaEtapaActualAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, venta_id):
        etapa = VentaEtapa.objects.filter(venta_id=venta_id).order_by("-timestamp").first()
        if not etapa:
            return Response({"estado": "sin_etapas"})
        return Response({
            "venta": venta_id,
            "estado_actual": etapa.etapa,
            "descripcion": etapa.get_etapa_display(),
            "timestamp": etapa.timestamp
        })
