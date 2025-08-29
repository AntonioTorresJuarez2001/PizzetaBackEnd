import random
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from usuarios.utils.roles import check_dueno
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema



from usuarios.models import (
    UsuarioPizzeriaRol,
    DuenoPizzeria,
    TokenNumericoPlano,
    UserProfile
)
from usuarios.serializers import (
    UsuarioPizzeriaRolSerializer,
    TokenNumericoPlanoSerializer,
    UserProfileSerializer
)
from pizzerias.models import Pizzeria

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


class UsuarioPizzeriaRolListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UsuarioPizzeriaRolSerializer

    def get_queryset(self):
        # Evitar que Swagger ejecute lógica que depende de kwargs
        if getattr(self, 'swagger_fake_view', False):
            return UsuarioPizzeriaRol.objects.none()

        pizzeria_id = self.kwargs["pizzeria_id"]

        # Validar que el usuario tenga permiso sobre esta pizzería
        try:
            check_dueno(self.request.user, pizzeria_id)
        except PermissionDenied:
            return UsuarioPizzeriaRol.objects.none()

        return UsuarioPizzeriaRol.objects.filter(pizzeria_id=pizzeria_id)



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

def generar_pin():
    """Genera un PIN aleatorio de 6 dígitos."""
    return f"{random.randint(0, 999999):06d}"

class EstablecerPinPlanoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["PIN"],
        operation_description="Establece o actualiza el PIN de 6 dígitos del usuario autenticado.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["pin"],
            properties={
                "pin": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="PIN numérico de 6 dígitos."
                ),
            },
        ),
        responses={
            200: openapi.Response("PIN actualizado correctamente"),
            400: openapi.Response("PIN inválido"),
        },
    )
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

    @swagger_auto_schema(
        tags=["PIN"],
        operation_description="Consulta el PIN actual del usuario autenticado. ",
        responses={
            200: openapi.Response(
                "PIN actual o null si no está configurado",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "pin": openapi.Schema(type=openapi.TYPE_STRING, description="PIN numérico o null")
                    }
                )
            ),
        },
    )
    def get(self, request):
        try:
            pin_obj = TokenNumericoPlano.objects.get(user=request.user)
            return Response({"pin": pin_obj.pin})
        except TokenNumericoPlano.DoesNotExist:
            return Response({"pin": None})


@csrf_exempt
@swagger_auto_schema(
    method="post",
    tags=["PIN"],
    operation_description="Verifica si el PIN ingresado es correcto y lo invalida generando uno nuevo automáticamente.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["pin"],
        properties={
            "pin": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="PIN numérico de 6 dígitos."
            ),
        },
    ),
    responses={
        200: openapi.Response("PIN válido y reemplazado"),
        400: openapi.Response("PIN inválido"),
        403: openapi.Response("PIN incorrecto"),
        404: openapi.Response("PIN no configurado"),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verificar_pin_plano(request):
    user = request.user
    pin_recibido = request.data.get("pin")

    if not pin_recibido or len(pin_recibido) != 6 or not pin_recibido.isdigit():
        return Response({"error": "PIN inválido"}, status=400)

    try:
        pin_obj = user.pin_plano
    except TokenNumericoPlano.DoesNotExist:
        return Response({"error": "PIN no configurado"}, status=404)

    if pin_obj.pin != pin_recibido:
        return Response({"error": "PIN incorrecto"}, status=403)

    nuevo_pin = generar_pin()
    pin_obj.pin = nuevo_pin
    pin_obj.save()

    return Response({"mensaje": "PIN válido y reemplazado"})
