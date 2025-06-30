from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ventas.models import Producto, Venta, VentaProducto, Pizzeria
from datetime import datetime
from django.db.models import Q

class Command(BaseCommand):
    help = "Elimina productos y ventas falsas generadas entre 2021 y 2025 para un usuario"

    def add_arguments(self, parser):
        parser.add_argument('--usuario', type=str, required=True, help='Username del dueño')
        parser.add_argument('--confirmar', action='store_true', help='Borrar sin pedir confirmación')

    def handle(self, *args, **options):
        username = options['usuario']
        confirmar = options['confirmar']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Usuario '{username}' no existe"))
            return

        pizzerias = Pizzeria.objects.filter(dueno_asignaciones__dueno=user)
        if not pizzerias.exists():
            self.stdout.write(self.style.WARNING("⚠️ Usuario no tiene pizzerías asignadas."))
            return

        fecha_inicio = datetime(2021, 1, 1)
        fecha_fin = datetime(2025, 12, 16)

        total_productos = 0
        total_ventas = 0

        for p in pizzerias:
            productos_falsos = Producto.objects.filter(
                pizzeria=p,
                descripcion__regex=r'^[A-Z][a-z]+ .*',
                precio__gte=40,
                precio__lte=200,
                created_at__year__lte=2025
            )
            ventas_falsas = Venta.objects.filter(
                pizzeria=p,
                dueno=user,
                fecha__range=(fecha_inicio, fecha_fin)
            )

            if not confirmar:
                self.stdout.write(f"\n📝 Pizzería: {p.nombre}")
                self.stdout.write(f"- Productos candidatos a eliminar: {productos_falsos.count()}")
                self.stdout.write(f"- Ventas candidatas a eliminar: {ventas_falsas.count()}")
            else:
                # Eliminar ventas y sus items
                count_ventas = ventas_falsas.count()
                VentaProducto.objects.filter(venta__in=ventas_falsas).delete()
                ventas_falsas.delete()

                # Eliminar productos
                count_productos = productos_falsos.count()
                productos_falsos.delete()

                total_productos += count_productos
                total_ventas += count_ventas

        if confirmar:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Eliminados: {total_productos} productos y {total_ventas} ventas falsas"))
        else:
            self.stdout.write("\n⚠️ Ejecuta con --confirmar para borrar realmente los datos.")
