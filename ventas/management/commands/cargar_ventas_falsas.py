from django.core.management.base import BaseCommand
from ventas.models import Pizzeria, DuenoPizzeria, Producto, Venta, VentaProducto
from django.contrib.auth.models import User
from faker import Faker
from random import randint, uniform, choice
from datetime import datetime, timedelta
import pytz

fake = Faker()
canales = ['DOMICILIO', 'LLEVAR', 'MOSTRADOR', 'PLATAFORMAS']
metodos_pago = ['EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'VALES']

def random_fecha_entre_2021_2025():
    inicio = datetime(2021, 1, 1)
    fin = datetime(2025, 12, 31, 23, 59)
    delta = fin - inicio
    random_seconds = randint(0, int(delta.total_seconds()))
    fecha_random = inicio + timedelta(seconds=random_seconds)
    return fecha_random  # ← sin tz



class Command(BaseCommand):
    help = "Genera ventas falsas con productos existentes entre 2021 y 2025"

    def add_arguments(self, parser):
        parser.add_argument('--usuario', type=str, required=True, help='Username del dueño de las pizzerías')
        parser.add_argument('--cantidad', type=int, default=20, help='Cantidad de ventas por pizzería')

    def handle(self, *args, **options):
        username = options['usuario']
        cantidad = options['cantidad']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Usuario '{username}' no existe"))
            return

        pizzerias = Pizzeria.objects.filter(dueno_asignaciones__dueno=user)
        if not pizzerias.exists():
            self.stderr.write(self.style.ERROR("No hay pizzerías asignadas a este usuario"))
            return

        total_generadas = 0
        for pizzeria in pizzerias:
            productos = Producto.objects.filter(pizzeria=pizzeria, activo=True)
            if productos.count() == 0:
                self.stdout.write(self.style.WARNING(f"Pizzería '{pizzeria.nombre}' no tiene productos activos. Se omite."))
                continue

            for _ in range(cantidad):
                fecha = random_fecha_entre_2021_2025()
                canal = choice(canales)
                metodo = choice(metodos_pago)

                items = []
                total = 0.0

                for _ in range(randint(1, 3)):
                    producto = choice(productos)
                    cantidad_producto = randint(1, 59)
                    subtotal = float(producto.precio) * cantidad_producto
                    total += subtotal
                    items.append((producto, cantidad_producto))

                venta = Venta.objects.create(  # ✅ aquí estaba el problema
                    pizzeria=pizzeria,
                    dueno=user,
                    fecha=fecha,
                    total=round(total, 2),
                    canal=canal,
                    metodo_pago=metodo
                )

                for producto, cantidad in items:
                    VentaProducto.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad
                    )

                total_generadas += 1

            self.stdout.write(self.style.SUCCESS(
                f"{cantidad} ventas generadas para '{pizzeria.nombre}'"
            ))

        self.stdout.write(self.style.SUCCESS(f"✅ Total de ventas generadas: {total_generadas}"))
