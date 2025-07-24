# ventas/views.py
from rest_framework import generics, permissions, status, serializers
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Sum, ProtectedError, Count
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from datetime import datetime
from .permissions import EmpleadoSoloLecturaPermission
from django.utils.timezone import now, timedelta
from .models import Pizzeria, Venta, DuenoPizzeria, Producto, VentaEtapa, UsuarioPizzeriaRol, User
from .serializers import (
    PizzeriaSerializer,
    VentaSerializer,
    ProductoSerializer,
    VentaEtapaSerializer,
    UsuarioPizzeriaRolSerializer
)
from drf_yasg.utils import swagger_auto_schema
# ventas/views.py

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import TokenNumericoPlano

# ——————————————————————————————————————————
# Utilidad para validar dueño de pizzería
# ——————————————————————————————————————————
def check_dueno(user, pizzeria_id):
    if not DuenoPizzeria.objects.filter(dueno=user, pizzeria_id=pizzeria_id).exists():
        raise PermissionDenied("No tienes permiso para acceder a esta pizzería.")


# ——————————————————————————————————————————
# 0) Usuario autenticado
# ------------------------------------------
@swagger_auto_schema(
    method='get', 
    tags=["Token y Usuarios"], 
    operation_description="Devuelve los datos del usuario autenticado, incluyendo ID, nombre de usuario, email y rol asignado."
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    u = request.user
    perfil = getattr(u, "perfil", None)

    return Response({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "rol": perfil.rol if perfil else "normal"
    })

# 1) CRUD Unidades (Pizzerías)
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

# ------------------------------------------
# 2) CRUD Ventas
# ------------------------------------------
class VentaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, EmpleadoSoloLecturaPermission]
    serializer_class = VentaSerializer

    @swagger_auto_schema(tags=["Ventas"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Ventas"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        pizzeria_id = self.kwargs["pizzeria_id"]
        check_dueno(self.request.user, pizzeria_id)
        return Venta.objects.filter(pizzeria_id=pizzeria_id).order_by("-fecha")

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
    permission_classes = [IsAuthenticated, EmpleadoSoloLecturaPermission]
    serializer_class = VentaSerializer
    lookup_url_kwarg = "venta_id"

    @swagger_auto_schema(tags=["Ventas"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Ventas"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Ventas"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Venta.objects.filter(
            pizzeria__dueno_asignaciones__dueno=self.request.user
        )


class VentaRetrieveUpdateDestroyByPizzeriaAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, EmpleadoSoloLecturaPermission]
    serializer_class = VentaSerializer
    lookup_url_kwarg = "venta_id"

    @swagger_auto_schema(tags=["Ventas"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Ventas"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(tags=["Ventas"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Ventas"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

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

class VentaRetrieveAPIView(RetrieveAPIView):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
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
    lookup_url_kwarg = "pk"

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
@swagger_auto_schema(method='get', tags=["Ventas Estadistica/Resumen"])
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
        # Obtener el lunes de la semana actual (inicio de semana)
        dias_desde_lunes = hoy.weekday()  # 0=lunes, 6=domingo
        inicio = hoy - timedelta(days=dias_desde_lunes)
        fin = inicio + timedelta(days=7)  # Hasta el domingo (inclusive)
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
    permission_classes = [permissions.IsAuthenticated, EmpleadoSoloLecturaPermission]
    serializer_class = VentaEtapaSerializer

    @swagger_auto_schema(tags=["Etapas de Venta"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        venta = serializer.validated_data["venta"]
        etapa = serializer.validated_data["etapa"]

        if venta.dueno != self.request.user:
            raise PermissionDenied("No puedes registrar eventos de una venta que no te pertenece.")

        if VentaEtapa.objects.filter(venta=venta, etapa=etapa).exists():
            raise ValidationError(f"Ya se registró la etapa '{etapa}' para esta venta.")

        # Validación por canal
        etapas_envio = {"envio_inicio", "regreso_repartidor"}
        if etapa in etapas_envio and venta.canal not in {"DOMICILIO", "LLEVAR", "DELIVERY"}:
            raise ValidationError(f"La etapa '{etapa}' solo aplica a ventas a domicilio o para llevar.")

        serializer.save(timestamp=serializer.validated_data.get("timestamp", now()))


class VentaEtapaListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VentaEtapaSerializer

    @swagger_auto_schema(tags=["Etapas de Venta"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        venta_id = self.kwargs["venta_id"]
        return VentaEtapa.objects.filter(venta_id=venta_id).order_by("timestamp")


class VentaEtapaDuracionesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(tags=["Etapas de Venta"])
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

    @swagger_auto_schema(tags=["Etapas de Venta"])
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
        
@swagger_auto_schema(method='get', tags=["Ventas Estadistica/Resumen"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ventas_por_dia(request):
    user = request.user
    rango = request.query_params.get("rango", "hoy")
    tipo = request.query_params.get("tipo", "total")  # 'total' o 'cantidad'
    hoy = now().date()
    inicio = hoy
    fin = hoy + timedelta(days=1)

    if rango == "hoy":
        inicio = hoy
        fin = hoy + timedelta(days=1)
    elif rango == "ayer":
        ayer = hoy - timedelta(days=1)
        inicio = ayer
        fin = hoy  # hasta hoy (sin incluir)
    elif rango == "semana":
        # Obtener el lunes de la semana actual (inicio de semana)
        dias_desde_lunes = hoy.weekday()  # 0=lunes, 6=domingo
        inicio = hoy - timedelta(days=dias_desde_lunes)
        fin = inicio + timedelta(days=7)  # Hasta el domingo (inclusive)
    elif rango == "mes":
        # Para mostrar todos los meses del año actual
        inicio = hoy.replace(month=1, day=1)
        fin = hoy.replace(month=12, day=31) + timedelta(days=1)
    elif rango == "anio":
        # Para mostrar los últimos 5 años
        anio_actual = hoy.year
        inicio = hoy.replace(year=anio_actual - 4, month=1, day=1)  # 5 años atrás
        fin = hoy.replace(year=anio_actual, month=12, day=31) + timedelta(days=1)
    # Puedes agregar más rangos si lo necesitas

    if tipo == "cantidad":
        # Contar ventas por día
        ventas = (
            Venta.objects
            .filter(pizzeria__dueno_asignaciones__dueno=user, fecha__date__gte=inicio, fecha__date__lt=fin)
            .annotate(dia=TruncDate('fecha'))
            .values('dia')
            .annotate(total=Count('id'))  # Contar ventas en lugar de sumar totales
            .order_by('dia')
        )
    else:
        # Sumar totales por día (comportamiento original)
        ventas = (
            Venta.objects
            .filter(pizzeria__dueno_asignaciones__dueno=user, fecha__date__gte=inicio, fecha__date__lt=fin)
            .annotate(dia=TruncDate('fecha'))
            .values('dia')
            .annotate(total=Sum('total'))
            .order_by('dia')
        )

    if rango == "semana":
        # Para semana, mostrar cada día con su fecha como label y nombre del día
        # Crear un diccionario con las ventas por fecha
        if tipo == "cantidad":
            ventas_por_fecha = {v["dia"]: int(v["total"]) for v in ventas}
        else:
            ventas_por_fecha = {v["dia"]: float(v["total"]) for v in ventas}
        
        # Nombres de los días de la semana en español
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        data = []
        # Generar datos para cada día de la semana (lunes a domingo)
        for i in range(7):
            fecha_dia = inicio + timedelta(days=i)
            if tipo == "cantidad":
                total_dia = ventas_por_fecha.get(fecha_dia, 0)
            else:
                total_dia = ventas_por_fecha.get(fecha_dia, 0.0)
            
            data.append({
                "label": dias_semana[i],  # Nombre del día para mostrar
                "fecha": fecha_dia.strftime("%d-%m-%Y"),  # Fecha real
                "total": total_dia,
                "dia_semana": i + 1  # 1=Lunes, 7=Domingo
            })
        
        # Debug: imprimir en consola lo que estamos devolviendo
        print(f"=== DEBUG VENTAS SEMANA ===")
        print(f"Rango recibido: {rango}")
        print(f"Tipo: {tipo}")
        print(f"Inicio: {inicio}, Fin: {fin}")
        print(f"Ventas DB: {list(ventas)}")
        print(f"Data final que se envía al frontend: {data}")
        print("=== FIN DEBUG ===")
    elif rango == "mes":
        # Para mes, agrupar por mes y mostrar los 12 meses del año
        
        # Reagrupar ventas por mes
        if tipo == "cantidad":
            ventas_por_mes = (
                Venta.objects
                .filter(pizzeria__dueno_asignaciones__dueno=user, fecha__date__gte=inicio, fecha__date__lt=fin)
                .annotate(mes=TruncMonth('fecha'))
                .values('mes')
                .annotate(total=Count('id'))  # Contar ventas
                .order_by('mes')
            )
        else:
            ventas_por_mes = (
                Venta.objects
                .filter(pizzeria__dueno_asignaciones__dueno=user, fecha__date__gte=inicio, fecha__date__lt=fin)
                .annotate(mes=TruncMonth('fecha'))
                .values('mes')
                .annotate(total=Sum('total'))  # Sumar totales
                .order_by('mes')
            )
        
        # Crear diccionario con ventas por mes
        if tipo == "cantidad":
            ventas_mes_dict = {v["mes"].month: int(v["total"]) for v in ventas_por_mes if v["mes"]}
        else:
            ventas_mes_dict = {v["mes"].month: float(v["total"]) for v in ventas_por_mes if v["mes"]}
        
        # Nombres de los meses en español
        meses_nombres = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        
        data = []
        # Generar datos para cada mes del año (1-12)
        for i in range(1, 13):
            if tipo == "cantidad":
                total_mes = ventas_mes_dict.get(i, 0)
            else:
                total_mes = ventas_mes_dict.get(i, 0.0)
            
            data.append({
                "label": meses_nombres[i-1],  # Nombre del mes para mostrar
                "mes": i,  # Número del mes (1-12)
                "total": total_mes,
                "anio": hoy.year  # Año actual
            })
        
        # Debug: imprimir en consola lo que estamos devolviendo
        print(f"=== DEBUG VENTAS MES ===")
        print(f"Rango recibido: {rango}")
        print(f"Inicio: {inicio}, Fin: {fin}")
        print(f"Ventas DB por mes: {list(ventas_por_mes)}")
        print(f"Data final que se envía al frontend: {data}")
        print("=== FIN DEBUG ===")
    elif rango == "anio":
        # Para año, agrupar por año y mostrar los últimos 5 años
        
        # Reagrupar ventas por año
        if tipo == "cantidad":
            ventas_por_anio = (
                Venta.objects
                .filter(pizzeria__dueno_asignaciones__dueno=user, fecha__date__gte=inicio, fecha__date__lt=fin)
                .annotate(anio=TruncYear('fecha'))
                .values('anio')
                .annotate(total=Count('id'))  # Contar ventas
                .order_by('anio')
            )
        else:
            ventas_por_anio = (
                Venta.objects
                .filter(pizzeria__dueno_asignaciones__dueno=user, fecha__date__gte=inicio, fecha__date__lt=fin)
                .annotate(anio=TruncYear('fecha'))
                .values('anio')
                .annotate(total=Sum('total'))  # Sumar totales
                .order_by('anio')
            )
        
        # Crear diccionario con ventas por año
        if tipo == "cantidad":
            ventas_anio_dict = {v["anio"].year: int(v["total"]) for v in ventas_por_anio if v["anio"]}
        else:
            ventas_anio_dict = {v["anio"].year: float(v["total"]) for v in ventas_por_anio if v["anio"]}
        
        data = []
        anio_actual = hoy.year
        # Generar datos para los últimos 5 años
        for i in range(5):
            anio = anio_actual - (4 - i)  # Desde hace 5 años hasta el año actual
            if tipo == "cantidad":
                total_anio = ventas_anio_dict.get(anio, 0)
            else:
                total_anio = ventas_anio_dict.get(anio, 0.0)
            
            data.append({
                "label": str(anio),  # Año como string para mostrar
                "anio": anio,  # Año como número
                "total": total_anio
            })
        
        # Debug: imprimir en consola lo que estamos devolviendo
        print(f"=== DEBUG VENTAS AÑO ===")
        print(f"Rango recibido: {rango}")
        print(f"Inicio: {inicio}, Fin: {fin}")
        print(f"Años a mostrar: {anio_actual-4} a {anio_actual}")
        print(f"Ventas DB por año: {list(ventas_por_anio)}")
        print(f"Data final que se envía al frontend: {data}")
        print("=== FIN DEBUG ===")
    else:
        print(f"=== DEBUG OTROS RANGOS ===")
        print(f"Rango: {rango}")
        print(f"Tipo: {tipo}")
        if tipo == "cantidad":
            data = [
                {"label": v["dia"].strftime("%d-%m-%Y"), "total": int(v["total"])}
                for v in ventas
            ]
        else:
            data = [
                {"label": v["dia"].strftime("%d-%m-%Y"), "total": float(v["total"])}
                for v in ventas
            ]
        print(f"Data final: {data}")
        print("=== FIN DEBUG ===")
    
    return Response(data)

@swagger_auto_schema(method='get', tags=["Ventas Estadistica/Resumen"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ventas_ayer(request):
    """
    Endpoint para obtener todas las ventas de ayer con detalles completos
    """
    user = request.user
    hoy = now().date()
    ayer = hoy - timedelta(days=1)
    inicio_ayer = ayer
    fin_ayer = hoy  # Hasta hoy (sin incluir)
    
    # Obtener todas las ventas de ayer
    ventas = Venta.objects.filter(
        pizzeria__dueno_asignaciones__dueno=user,
        fecha__date__gte=inicio_ayer,
        fecha__date__lt=fin_ayer
    ).order_by('-fecha')
    
    # Serializar las ventas
    serializer = VentaSerializer(ventas, many=True)
    
    # Calcular totales
    total_ventas = ventas.aggregate(total=Sum('total'))['total'] or 0
    cantidad_ventas = ventas.count()
    
    return Response({
        "fecha": str(ayer),
        "cantidad_ventas": cantidad_ventas,
        "total_ventas": float(total_ventas),
        "ventas": serializer.data
    })

# ventas/views.py

class UsuarioPizzeriaRolListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UsuarioPizzeriaRolSerializer

    def get_queryset(self):
        return UsuarioPizzeriaRol.objects.filter(
            pizzeria__dueno_asignaciones__dueno=self.request.user
        ).select_related("user", "pizzeria")

    def perform_create(self, serializer):
        pizzeria_obj = serializer.validated_data.get("pizzeria")

        if not pizzeria_obj:
            raise serializers.ValidationError("Se requiere una pizzería válida.")

        check_dueno(self.request.user, pizzeria_obj.id)
        serializer.save()

class UsuarioPizzeriaRolRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UsuarioPizzeriaRol.objects.all()
    serializer_class = UsuarioPizzeriaRolSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "rol_id"  # <- Esto permite que siga usando <int:rol_id> en la URL


    def put(self, request, rol_id):
        instance = self.get_object()
        perfil = getattr(request.user, "perfil", None)

        if not perfil:
            return Response({"error": "Perfil no encontrado."}, status=400)

        rol_actual = perfil.rol

        # Validar permisos
        if rol_actual in ["gerente", "subgerente"]:
            if not UsuarioPizzeriaRol.objects.filter(
                user=request.user,
                pizzeria=instance.pizzeria,
                rol=rol_actual
            ).exists():
                return Response(
                    {"error": "No puedes editar empleados fuera de tu pizzería asignada."},
                    status=403
                )

        elif rol_actual not in ["admin", "dueno", "gerente", "subgerente"]:
            return Response({"error": "No tienes permisos para editar usuarios."}, status=403)

        data = request.data.copy()

        # Prevenir cambio de usuario
        data["user"] = instance.user.id

        # Dueños solo pueden asignar pizzerías que les pertenecen
        if rol_actual == "dueno":
            try:
                check_dueno(request.user, data.get("pizzeria"))
            except PermissionDenied:
                return Response({"error": "No puedes asignar esa pizzería."}, status=403)

        serializer = self.get_serializer(instance, data=data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
        
class CrearEmpleadoAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        pizzeria_id = data.get("pizzeria_id")
        rol_asignar = data.get("rol", "empleado")

        if not all([username, password, pizzeria_id]):
            return Response(
                {"error": "username, password y pizzeria_id son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        perfil = getattr(request.user, "perfil", None)
        if not perfil:
            return Response({"error": "Perfil no encontrado."}, status=400)

        rol_actual = perfil.rol

        # Validar jerarquía permitida
        jerarquia = {
            "admin": ["admin", "dueno", "gerente", "subgerente", "empleado", "cajero"],
            "dueno": ["gerente", "subgerente", "empleado", "cajero"],
            "gerente": ["subgerente", "empleado", "cajero",],
            "subgerente": ["empleado", "cajero"],
        }

        if rol_actual not in jerarquia:
            return Response({"error": "No tienes permiso para crear usuarios."}, status=403)

        if rol_asignar not in jerarquia[rol_actual]:
            return Response({
                "error": f"No puedes asignar el rol '{rol_asignar}'. Solo puedes asignar: {', '.join(jerarquia[rol_actual])}."
            }, status=403)

        # Validar control sobre la pizzería según su rol
        if rol_actual == "admin":
            pass  # acceso total

        elif rol_actual == "dueno":
            try:
                check_dueno(request.user, pizzeria_id)
            except PermissionDenied:
                return Response({"error": "No tienes permiso sobre esa pizzería."}, status=403)

        elif rol_actual in ["gerente", "subgerente"]:
            tiene_permiso = UsuarioPizzeriaRol.objects.filter(
                user=request.user,
                pizzeria_id=pizzeria_id,
                rol=rol_actual
            ).exists()
            if not tiene_permiso:
                return Response({
                    "error": f"Solo puedes agregar usuarios a la pizzería donde eres {rol_actual}."
                }, status=403)

        # Validar que no exista el usuario
        if User.objects.filter(username=username).exists():
            return Response({"error": "Ya existe un usuario con ese username."}, status=400)

        # Crear el usuario
        user = User.objects.create_user(username=username, password=password, email=email or "")

        # Asignar el rol a esa pizzería
        pizzeria = Pizzeria.objects.get(id=pizzeria_id)
        UsuarioPizzeriaRol.objects.create(user=user, pizzeria=pizzeria, rol=rol_asignar)

        return Response({"mensaje": "Empleado creado y asignado correctamente."}, status=201)

class EmpleadosDelDuenoAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UsuarioPizzeriaRolSerializer

    def get_queryset(self):
        user = self.request.user
        pizzeria_id = self.request.query_params.get("pizzeria_id")

        queryset = UsuarioPizzeriaRol.objects.select_related("user", "pizzeria")

        # Si se pasa un pizzeria_id, filtra por esa pizzería
        if pizzeria_id:
            try:
                check_dueno(user, pizzeria_id)
            except PermissionDenied:
                return UsuarioPizzeriaRol.objects.none()

            return queryset.filter(pizzeria_id=pizzeria_id)

        #  Si no se pasa pizzeria_id, trae todos los empleados del dueño
        return queryset.filter(pizzeria__dueno_asignaciones__dueno=user)


class EstablecerPinPlanoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pin = request.data.get("pin")

        if not pin or not pin.isdigit() or len(pin) != 6:
            return Response({"error": "El PIN debe tener 6 dígitos numéricos."}, status=400)

        pin_obj, _ = TokenNumericoPlano.objects.get_or_create(user=request.user)
        pin_obj.pin = pin
        pin_obj.save()

        return Response({"mensaje": "PIN Actualizado correctamente."})

class ConsultarPinPlanoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            pin_obj = TokenNumericoPlano.objects.get(user=request.user)
            return Response({"pin": pin_obj.pin})
        except TokenNumericoPlano.DoesNotExist:
            return Response({"pin": None})

@csrf_exempt  # ← necesario para permitir POST desde frontend sin CSRF token
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verificar_pin_plano(request):
    """
    Verifica si el PIN ingresado es correcto para el usuario autenticado.
    """
    user = request.user
    pin_recibido = request.data.get("pin")

    if not pin_recibido or len(pin_recibido) != 6:
        return Response({"error": "PIN inválido"}, status=400)

    try:
        pin_obj = user.pin_plano  # ← relacionado con related_name en el modelo
    except TokenNumericoPlano.DoesNotExist:
        return Response({"error": "PIN no configurado"}, status=404)

    if pin_obj.pin == pin_recibido:
        return Response({"mensaje": "PIN válido"})
    else:
        return Response({"error": "PIN incorrecto"}, status=403)
