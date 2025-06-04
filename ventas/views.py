# ventas/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Pizzeria, Venta, DuenoPizzeria
from .serializers import PizzeriaSerializer, VentaSerializer
# ventas/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


class ListaPizzeriasUsuario(generics.ListAPIView):
    """
    Lista las pizzerías asociadas al usuario autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PizzeriaSerializer

    def get_queryset(self):
        return Pizzeria.objects.filter(dueño_asignaciones__dueno=self.request.user)

class ListaVentasPorPizzeria(APIView):
    """
    Lista las ventas de una pizzería, solo si el usuario autenticado
    está asociado a ella.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pizzeria_id):
        try:
            # Validar que el usuario esté asociado a la pizzería
            DuenoPizzeria.objects.get(
                dueno=request.user,
                pizzeria_id=pizzeria_id
            )
        except DuenoPizzeria.DoesNotExist:
            return Response(
                {"detalle": "Pizzería no encontrada o sin permiso"},
                status=status.HTTP_404_NOT_FOUND
            )

        ventas_qs = Venta.objects.filter(pizzeria_id=pizzeria_id).order_by("-fecha")
        serializer = VentaSerializer(ventas_qs, many=True)
        return Response(serializer.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Devuelve información mínima del usuario que hizo la petición.
    """
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
    })
