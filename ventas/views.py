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
from usuarios.permissions import EmpleadoSoloLecturaPermission
from django.utils.timezone import now, timedelta
from .models import Venta, VentaEtapa, VentaProducto
from pizzerias.models import Pizzeria
from productos.models import Producto
from .serializers import (
    VentaSerializer,
    VentaEtapaSerializer,
    ProductoSerializer
)
import requests
from .services.firebird_hctaord import get_hctaord, get_producto_firebird

from drf_yasg.utils import swagger_auto_schema
# ventas/views.py
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from usuarios.models import DuenoPizzeria
from usuarios.utils.roles import check_dueno
from django.db import transaction

# ------------------------------------------
# 2) CRUD Ventas
# ------------------------------------------
class VentaListCreateAPIView(generics.ListCreateAPIView):
    """
    API para listar y registrar ventas de una pizzería específica.

    Flujo recomendado para integradores externos:
    1. **Registrar o consultar productos existentes**
       - Endpoint: `POST /pizzerias/{pizzeria_id}/productos/`
       - El campo `id_externo` puede ser usado para relacionar productos con catálogos de nartin.
       - `id_externo` es opcional y puede ser `null` para productos propios no presentes en el catálogo base.
       - El mismo `id_externo` puede repetirse en distintas pizzerías.

    2. **Registrar la venta**
       - Endpoint: `POST /pizzerias/{pizzeria_id}/ventas/`
       - En `items.producto` se debe enviar el **ID interno** del producto mio (no `id_externo` que es el id_prod).
       - `producto_detalle` es opcional y puede incluir información del producto, o dejar que la API la genere.

    Ejemplo de request para registrar una venta:

    {
      "canal": "Mostrador",
      "metodo_pago": "Efectivo",
      "items": [
        {
          "producto": 181,  # ID interno del producto en el sistema
          "producto_detalle": {
            "id_externo": 1234512345,  # Puede ser null si es producto propio o con numero si viene de cat Martin
            "nombre": "Pizza Mediana Toño",
            "precio": "159.00",
            "categoria": "Pizza",
            "descripcion": "Masa delgada",
            "activo": true
          },
          "cantidad": 2
        }
      ]
    }

    Notas:
    - `id_externo` puede ser omitido o `null` si el producto es propio.
    - Al registrar una venta, el sistema crea automáticamente la etapa inicial "toma_pedido_inicio".
    """
    permission_classes = [IsAuthenticated, EmpleadoSoloLecturaPermission]
    serializer_class = VentaSerializer

    @swagger_auto_schema(
        tags=["Ventas"],
        operation_summary="Lista o registra ventas",
        operation_description="""
        Lista todas las ventas de una pizzería o registra una nueva.

        Notas importantes:
        - `items.producto` debe ser el ID interno del producto en la pizzería.
        - `id_externo` es opcional en `producto_detalle` y puede ser `null`.
        - El sistema crea automáticamente una etapa "toma_pedido_inicio" al registrar una venta.
        """,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["Ventas"],
        operation_summary="Registrar una nueva venta",
        request_body=VentaSerializer,
        responses={201: "Venta creada correctamente"},
    )
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


class FirebirdHctaordProxyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _fmt_fecha_firebird(n):
        """Convierte 45109 -> 'YYYY-MM-DD' (base 1899-12-30)."""
        try:
            base = datetime(1899, 12, 30)
            return (base + timedelta(days=int(n))).strftime("%Y-%m-%d")
        except Exception:
            return n

    @staticmethod
    def _format_row(row):
        # Formateo opcional
        if isinstance(row.get("Fecha"), int):
            row["FechaISO"] = FirebirdHctaordProxyAPIView._fmt_fecha_firebird(row["Fecha"])
        # Redondear montos si existen
        for k in ["M_Importe", "M_Total", "M_Neto", "M_Imp", "M_Imp_Desc", "P_Imp1", "P_Imp2", "Precio_Unit", "Precio_Modif"]:
            if row.get(k) is not None:
                try:
                    row[k] = float(round(float(row[k]), 2))
                except Exception:
                    pass
        # Hora a HH:MM:SS si viene como datetime string
        if isinstance(row.get("Hora"), str) and "T" in row["Hora"]:
            try:
                row["Hora"] = row["Hora"].split("T")[1][:8]
            except Exception:
                pass
        return row

    @swagger_auto_schema(operation_summary="Proxy: Hctaord Firebird (solo lectura)")
    def get(self, request, pizzeria_id):
        """
        GET /api/pizzerias/{pizzeria_id}/firebird/hctaord/
          - Pasa filtros como query params: id_pro, id_emp, id_cta, id_linea, grupo, fecha_ini, fecha_fin
          - Opcional: id_local (si no está mapeado en el modelo Pizzeria)
          - Opcional: detalle de una cuenta => incluir id_cta y fecha
          - Opcional: format=1 (devuelve campos con formateo amigable)
        """
        # Seguridad: validar dueño
        check_dueno(request.user, pizzeria_id)

        # Resolver id_local Firebird
        pizzeria = Pizzeria.objects.get(pk=pizzeria_id)
        id_local = request.query_params.get("id_local")
        if not id_local:
            # Si tu modelo Pizzeria ya tiene relación al local de Firebird, úsala:
            id_local = getattr(pizzeria, "id_local_firebird", None)
        if not id_local:
            return Response(
                {"detail": "Falta id_local. Pásalo como query param ?id_local=4 o agrega 'id_local_firebird' a Pizzeria."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si piden una cuenta específica
        id_cta = request.query_params.get("id_cta")
        fecha = request.query_params.get("fecha")  # valor Firebird (número de días). Si prefieres ISO, luego mapeamos.

        # Filtros permitidos
        allowed = {"id_pro", "id_emp", "id_linea", "grupo", "fecha_ini", "fecha_fin", "min_total", "max_total"}
        params = {k: v for k, v in request.query_params.items() if k in allowed}

        try:
            if id_cta and not fecha:
                return Response({"detail": "Si envías id_cta, debes enviar también 'fecha' (formato Firebird)."}, status=400)

            if id_cta and fecha:
                data = get_hctaord(id_local=id_local, fecha=fecha, id_cta=id_cta, params=params)
            else:
                data = get_hctaord(id_local=None, fecha=None, id_cta=None, params={"id_local": id_local, **params})

            # ¿Formatear?
            if request.query_params.get("format") == "1":
                if isinstance(data, list):
                    data = [self._format_row(d) for d in data]
                elif isinstance(data, dict):
                    data = self._format_row(data)

            return Response(data)

        except requests.HTTPError as e:
            return Response({"error": f"Firebird respondió {e.response.status_code}", "detail": str(e)}, status=502)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class FirebirdImportVentaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pizzeria_id):
        """
        Importa una venta desde Firebird (tabla Hctaord) a Pizzeta.
        Requiere query params: id_local, fecha (Firebird), id_cta.
        - Si falta un producto en Pizzeta => devuelve advertencia y NO crea la venta.
        """
        id_local = request.query_params.get("id_local")
        fecha = request.query_params.get("fecha")
        id_cta = request.query_params.get("id_cta")
        Id_Ord = request.query_params.get("Id_Ord")

        if not (id_local and fecha and id_cta):
            return Response(
                {"detail": "Debes enviar id_local, fecha (Firebird) e id_cta"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Llamar Firebird
        try:
            registros = get_hctaord(id_local=id_local, fecha=fecha, id_cta=id_cta)
        except Exception as e:
            return Response({"error": f"Error al obtener datos de Firebird: {str(e)}"}, status=502)

        if not registros:
            return Response({"detail": "No se encontraron registros en Hctaord"}, status=404)

        pizzeria = Pizzeria.objects.get(pk=pizzeria_id)
        folio_ticket = f"{fecha}{id_local}{id_cta}"

        # Validar si ya existe
        if Venta.objects.filter(pizzeria=pizzeria, folio_ticket=folio_ticket).exists():
            return Response(
                {"detail": "La venta ya existe en Pizzeta", "folio_ticket": folio_ticket},
                status=status.HTTP_200_OK
            )

        # Verificar productos
        faltantes = []
        for r in registros:
            id_pro = r.get("Id_Pro")
            if not Producto.objects.filter(pizzeria=pizzeria, id_externo=id_pro).exists():
                faltantes.append({
                    "id_pro": id_pro,
                    "producto": r.get("Producto"),
                    "precio_unit": r.get("Precio_Unit"),
                    "linea": r.get("Linea")
                })

        if faltantes:
            return Response(
                {
                    "detail": "Existen productos en Firebird que no están en Pizzeta.",
                    "faltantes": faltantes
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear venta y items
        with transaction.atomic():
            total = sum(r.get("M_Total") or 0 for r in registros)

            venta = Venta.objects.create(
                pizzeria=pizzeria,
                dueno=request.user,
                fecha=now(),
                canal="MOSTRADOR",
                metodo_pago="EFECTIVO",
                folio_ticket=folio_ticket,
                total=total
            )

            for r in registros:
                producto = Producto.objects.get(pizzeria=pizzeria, id_externo=r.get("Id_Pro"))
                cantidad = int(r.get("Porciones") or 1)

                VentaProducto.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad
                )

            VentaEtapa.objects.create(
                venta=venta,
                etapa="toma_pedido_inicio",
                timestamp=now()
            )

        return Response(VentaSerializer(venta).data, status=201)

class CrearProductoDesdeFirebirdAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pizzeria_id, id_pro):
        """
        Crea un producto en Pizzeta basado en un producto de Firebird.
        """
        # Validar permisos
        check_dueno(request.user, pizzeria_id)
        pizzeria = Pizzeria.objects.get(pk=pizzeria_id)

        # Verificar si ya existe
        if Producto.objects.filter(pizzeria=pizzeria, id_externo=id_pro).exists():
            return Response(
                {"detail": f"El producto con id_externo={id_pro} ya existe en esta pizzería."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener datos de Firebird
        try:
            data = get_producto_firebird(id_pro)
        except Exception as e:
            return Response({"error": f"No se pudo obtener el producto {id_pro} de Firebird", "detail": str(e)},
                            status=status.HTTP_502_BAD_GATEWAY)

        # Crear producto en Pizzeta
        producto = Producto.objects.create(
            pizzeria=pizzeria,
            id_externo=data.get("id_pro", id_pro),
            nombre=data.get("nombre", f"Producto {id_pro}"),
            descripcion=data.get("descripcion", ""),
            precio=0,  # ⚠️ Ajusta si quieres traer precio de Firebird (si lo tienes disponible)
            categoria="Firebird",
            activo=True
        )

        return Response(ProductoSerializer(producto).data, status=status.HTTP_201_CREATED)
