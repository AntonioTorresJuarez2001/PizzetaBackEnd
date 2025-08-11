from rest_framework import generics, status
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from .models import Insumo, MovimientoInventario, Receta
from .serializers import (
    InsumoSerializer,
    MovimientoInventarioSerializer,
    RecetaSerializer,
    RecetaConIngredientesSerializer
)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator

# ========================
# 📦 INSUMOS
# ========================

@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Listar insumos",
        operation_description="Devuelve los insumos registrados en el sistema. Se puede filtrar por pizzería y estado activo.",
        manual_parameters=[
            openapi.Parameter(
                'pizzeria_id',
                openapi.IN_QUERY,
                description="ID de la pizzería para filtrar insumos",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'activo',
                openapi.IN_QUERY,
                description="Filtrar por estado activo (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Ordenar por campo (ej: nombre, -fecha_creacion)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: InsumoSerializer(many=True),
            400: "Parámetros de consulta inválidos",
            500: "Error interno del servidor"
        }
    )
)
@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Crear insumo",
        operation_description="Registra un nuevo insumo en el inventario de una pizzería.",
        responses={
            201: InsumoSerializer,
            400: "Error de validación en los datos enviados",
            500: "Error interno del servidor"
        }
    )
)
class InsumoListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar o crear insumos.
    
    GET: Lista todos los insumos, opcionalmente filtrados por pizzería y estado
    POST: Crea un nuevo insumo en el inventario
    
    Filtros disponibles:
    - pizzeria_id: Filtra insumos por pizzería específica
    - activo: Filtra por estado activo/inactivo
    - ordering: Permite ordenar los resultados
    """
    queryset = Insumo.objects.all()
    serializer_class = InsumoSerializer

    def get_queryset(self):
        """
        Permite filtrar los insumos por pizzería, estado activo y ordenamiento.
        Maneja errores de validación en los parámetros.
        """
        queryset = self.queryset
        
        # Filtro por pizzería
        pizzeria_id = self.request.query_params.get("pizzeria_id")
        if pizzeria_id:
            try:
                pizzeria_id = int(pizzeria_id)
                queryset = queryset.filter(pizzeria_id=pizzeria_id)
            except ValueError:
                # Si el ID no es válido, devolver queryset vacío
                return queryset.none()
        
        # Filtro por estado activo
        activo = self.request.query_params.get("activo")
        if activo is not None:
            if activo.lower() in ['true', '1']:
                queryset = queryset.filter(activo=True)
            elif activo.lower() in ['false', '0']:
                queryset = queryset.filter(activo=False)
        
        # Ordenamiento
        ordering = self.request.query_params.get("ordering")
        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except:
                # Si el ordenamiento no es válido, usar orden por defecto
                pass
        
        return queryset


@method_decorator(
    name='get', 
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Obtener insumo",
        operation_description="Devuelve los detalles de un insumo específico por su ID.",
        responses={
            200: InsumoSerializer,
            404: "Insumo no encontrado",
            500: "Error interno del servidor"
        }
    )
)
@method_decorator(
    name='put', 
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Actualizar insumo completo",
        operation_description="Actualiza todos los campos de un insumo específico.",
        responses={
            200: InsumoSerializer,
            400: "Error de validación en los datos",
            404: "Insumo no encontrado",
            500: "Error interno del servidor"
        }
    )
)
@method_decorator(
    name='patch', 
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Actualizar insumo parcial",
        operation_description="Actualiza campos específicos de un insumo.",
        responses={
            200: InsumoSerializer,
            400: "Error de validación en los datos",
            404: "Insumo no encontrado",
            500: "Error interno del servidor"
        }
    )
)
@method_decorator(
    name='delete', 
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Eliminar insumo",
        operation_description="Elimina un insumo del sistema.",
        responses={
            204: "Insumo eliminado exitosamente",
            404: "Insumo no encontrado",
            500: "Error interno del servidor"
        }
    )
)
class InsumoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para obtener, actualizar o eliminar un insumo por su ID.
    
    GET: Obtiene los detalles completos del insumo
    PUT: Actualiza todos los campos del insumo
    PATCH: Actualiza campos específicos del insumo
    DELETE: Elimina el insumo del sistema
    """
    queryset = Insumo.objects.all()
    serializer_class = InsumoSerializer


# ========================
# ⚙️ MOVIMIENTOS
# ========================

@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Listar movimientos de inventario",
        operation_description="Devuelve los movimientos registrados (entradas, salidas, ajustes). Se puede filtrar por pizzería y tipo de movimiento.",
        manual_parameters=[
            openapi.Parameter(
                'pizzeria_id',
                openapi.IN_QUERY,
                description="ID de la pizzería para filtrar movimientos",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'tipo_movimiento',
                openapi.IN_QUERY,
                description="Tipo de movimiento (entrada, salida, ajuste)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'insumo_id',
                openapi.IN_QUERY,
                description="ID del insumo para filtrar movimientos",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Ordenar por campo (ej: -fecha, cantidad)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: MovimientoInventarioSerializer(many=True),
            400: "Parámetros de consulta inválidos",
            500: "Error interno del servidor"
        }
    )
)
@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Registrar movimiento",
        operation_description="Registra un movimiento de inventario (entrada, salida o ajuste). Actualiza automáticamente el stock del insumo.",
        responses={
            201: MovimientoInventarioSerializer,
            400: "Error de validación en los datos enviados",
            500: "Error interno del servidor"
        }
    )
)
class MovimientoInventarioListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar o registrar movimientos manuales de inventario.
    
    GET: Lista todos los movimientos con información del insumo y usuario
    POST: Registra un nuevo movimiento y actualiza el stock automáticamente
    
    Filtros disponibles:
    - pizzeria_id: Filtra movimientos por pizzería específica
    - tipo_movimiento: Filtra por tipo (entrada, salida, ajuste)
    - insumo_id: Filtra movimientos de un insumo específico
    - ordering: Permite ordenar los resultados
    """
    queryset = MovimientoInventario.objects.all().select_related('insumo', 'usuario')
    serializer_class = MovimientoInventarioSerializer

    def get_queryset(self):
        """
        Permite filtrar los movimientos por pizzería, tipo, insumo y ordenamiento.
        Optimiza las consultas con select_related.
        """
        queryset = self.queryset
        
        # Filtro por pizzería
        pizzeria_id = self.request.query_params.get("pizzeria_id")
        if pizzeria_id:
            try:
                pizzeria_id = int(pizzeria_id)
                queryset = queryset.filter(pizzeria_id=pizzeria_id)
            except ValueError:
                return queryset.none()
        
        # Filtro por tipo de movimiento
        tipo_movimiento = self.request.query_params.get("tipo_movimiento")
        if tipo_movimiento:
            queryset = queryset.filter(tipo=tipo_movimiento)
        
        # Filtro por insumo
        insumo_id = self.request.query_params.get("insumo_id")
        if insumo_id:
            try:
                insumo_id = int(insumo_id)
                queryset = queryset.filter(insumo_id=insumo_id)
            except ValueError:
                return queryset.none()
        
        # Ordenamiento (por defecto más recientes primero)
        ordering = self.request.query_params.get("ordering", "-fecha")
        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except:
                queryset = queryset.order_by("-fecha")
        
        return queryset


# ========================
# 🍕 RECETAS
# ========================

@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Listar recetas",
        operation_description="Lista las recetas registradas en el sistema con sus ingredientes. Se puede filtrar por producto asociado.",
        manual_parameters=[
            openapi.Parameter(
                'producto_id',
                openapi.IN_QUERY,
                description="ID del producto asociado a la receta",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'activa',
                openapi.IN_QUERY,
                description="Filtrar por recetas activas (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Ordenar por campo (ej: nombre, -fecha_creacion)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: RecetaSerializer(many=True),
            400: "Parámetros de consulta inválidos",
            500: "Error interno del servidor"
        }
    )
)
class RecetaListView(generics.ListAPIView):
    """
    Vista para listar recetas con sus ingredientes.
    
    GET: Lista todas las recetas con ingredientes precargados para optimizar consultas
    
    Filtros disponibles:
    - producto_id: Filtra recetas por producto específico
    - activa: Filtra por estado activo/inactivo de la receta
    - ordering: Permite ordenar los resultados
    """
    queryset = Receta.objects.all().prefetch_related('ingredientes')
    serializer_class = RecetaSerializer

    def get_queryset(self):
        """
        Permite filtrar por producto_id, estado activo y ordenamiento.
        Optimiza consultas con prefetch_related para ingredientes.
        """
        queryset = self.queryset
        
        # Filtro por producto
        producto_id = self.request.query_params.get("producto_id")
        if producto_id:
            try:
                producto_id = int(producto_id)
                queryset = queryset.filter(producto_id=producto_id)
            except ValueError:
                return queryset.none()
        
        # Filtro por estado activo
        activa = self.request.query_params.get("activa")
        if activa is not None:
            if activa.lower() in ['true', '1']:
                queryset = queryset.filter(activa=True)
            elif activa.lower() in ['false', '0']:
                queryset = queryset.filter(activa=False)
        
        # Ordenamiento
        ordering = self.request.query_params.get("ordering", "producto__nombre")  # default sensato
        try:
            queryset = queryset.order_by(ordering)
        except Exception:
            queryset = queryset.order_by("-fecha_creacion")  # fallback válido
            
        return queryset


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Detalle de receta",
        operation_description="Devuelve los detalles completos de una receta específica, incluyendo todos sus ingredientes con cantidades.",
        responses={
            200: RecetaSerializer,
            404: "Receta no encontrada",
            500: "Error interno del servidor"
        }
    )
)
class RecetaDetailView(generics.RetrieveAPIView):
    """
    Vista para obtener el detalle completo de una receta específica.
    
    GET: Devuelve la receta con todos sus ingredientes y cantidades
    Optimiza la consulta precargando los ingredientes relacionados.
    """
    queryset = Receta.objects.all().prefetch_related('ingredientes')
    serializer_class = RecetaSerializer


@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=["Inventario"],
        operation_summary="Crear receta con ingredientes",
        operation_description="""
        Registra una nueva receta completa con sus ingredientes en una sola operación.
        
        Requiere:
        - ID del producto asociado
        - Lista de ingredientes con sus cantidades
        - Información básica de la receta (nombre, descripción, etc.)
        
        La operación es atómica: si falla algún ingrediente, se revierte toda la creación.
        """,
        responses={
            201: RecetaConIngredientesSerializer,
            400: "Error de validación en los datos enviados",
            500: "Error interno del servidor"
        }
    )
)
class RecetaCreateView(generics.CreateAPIView):
    """
    Vista para crear una receta completa con sus ingredientes anidados.
    
    POST: Crea una receta nueva junto con todos sus ingredientes
    
    Características:
    - Operación atómica (todo o nada)
    - Validación completa de ingredientes
    - Creación de relaciones automática
    - Respuesta con datos completos creados
    """
    queryset = Receta.objects.all()
    serializer_class = RecetaConIngredientesSerializer

    def create(self, request, *args, **kwargs):
        """
        Sobrescribe el método create para proporcionar mejor manejo de errores
        y respuestas más informativas.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED, 
                headers=headers
            )
        except ValidationError as e:
            return Response(
                {"error": "Error de validación", "details": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Error interno del servidor", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )