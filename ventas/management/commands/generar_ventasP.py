# ventas/management/commands/generar_ventas.py

from django.core.management.base import BaseCommand
from faker import Faker
from django.contrib.auth.models import User
from ventas.models import Pizzeria, DuenoPizzeria, Venta
import random
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = "Genera ventas falsas para Pizzería Miyana durante todo 2025"

    def handle(self, *args, **options):
        fake = Faker("es_MX")

        # 1) Crear (o recuperar) usuario “dueno_miyana”
        username = "Martin"
        email = ""
        password = "Pass123."
        dueno_miyana, creado = User.objects.get_or_create(
            username=username,
            defaults={"email": email}
        )
        if creado:
            dueno_miyana.set_password(password)
            dueno_miyana.save()
            self.stdout.write(f"Usuario dueño creado: {username}")
        else:
            self.stdout.write(f"Usuario dueño existente: {username}")

        # 2) Obtener (o crear) la Pizzería “Pizzería Miyana”
        nombre_objetivo = "Pizzería Miyana"
        direccion_falsa = fake.address().replace("\n", ", ")
        telefono_falso = fake.phone_number()[:20]
        pizzeria_miyana, creada_p = Pizzeria.objects.get_or_create(
            nombre=nombre_objetivo,
            defaults={
                "direccion": direccion_falsa,
                "telefono": telefono_falso
            }
        )
        if creada_p:
            self.stdout.write(f"Pizzería creada: {nombre_objetivo}")
        else:
            self.stdout.write(f"Pizzería existente: {nombre_objetivo}")

        # 3) Asignar el dueño a la pizzería (si no existe ya la relación)
        DuenoPizzeria.objects.get_or_create(
            dueno=dueno_miyana,
            pizzeria=pizzeria_miyana
        )
        self.stdout.write(f"Asignado dueño '{dueno_miyana.username}' a '{nombre_objetivo}'")

        # 4) Preparar rango de fechas para todo el 2025
        #    Creamos dos datetime aware (zona horaria del proyecto)
        tz = timezone.get_current_timezone()
        inicio_2025 = timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0), tz)
        fin_2025    = timezone.make_aware(datetime(2025, 12, 31, 23, 59, 59), tz)
        delta_total_segundos = int((fin_2025 - inicio_2025).total_seconds())

        # 5) Generar ventas falsas en ese rango de fechas
        metodos = ["EFECTIVO", "TARJETA", "OTRO"]
        # Por ejemplo, crearemos entre 50 y 100 ventas para todo el año
        num_ventas = random.randint(10, 16)

        for _ in range(num_ventas):
            # Elegimos un offset en segundos dentro de 2025
            segundos_aleatorios = random.randint(0, delta_total_segundos)
            fecha_aleatoria = inicio_2025 + timedelta(seconds=segundos_aleatorios)

            total = round(random.uniform(200.0, 2000.0), 2)
            metodo_pago = random.choice(metodos)

            Venta.objects.create(
                pizzeria=pizzeria_miyana,
                dueno=dueno_miyana,
                fecha=fecha_aleatoria,
                total=total,
                metodo_pago=metodo_pago
            )

        self.stdout.write(self.style.SUCCESS(
            f"Se han creado {num_ventas} ventas falsas para '{nombre_objetivo}' durante 2025."
        ))
