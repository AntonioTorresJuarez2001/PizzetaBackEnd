# ventas/management/commands/generar_ventas.py

from django.core.management.base import BaseCommand
from faker import Faker
from django.contrib.auth.models import User
from ventas.models import Pizzeria, DuenoPizzeria, Venta
import random
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = "Genera datos falsos (usuarios, pizzerías, dueños y ventas)"

    def handle(self, *args, **options):
        fake = Faker("es_MX")

        # 1) Crear usuarios “dueños”
        usuarios = []
        for _ in range(5):
            username = fake.user_name()[:30]
            email = fake.email()
            password = "Pass123!"
            u = User.objects.create_user(username=username, email=email, password=password)
            usuarios.append(u)
            self.stdout.write(f"Usuario creado: {username}")

        # 2) Crear pizzerías
        pizzerias = []
        for _ in range(10):
            nombre = fake.company()[:100]
            direccion = fake.address().replace("\n", ", ")
            telefono = fake.phone_number()[:20]
            p = Pizzeria.objects.create(
                nombre=nombre,
                direccion=direccion,
                telefono=telefono
            )
            pizzerias.append(p)
            self.stdout.write(f"Pizzería creada: {nombre}")

        # 3) Asignar dueños a pizzerías (usar los campos sin tilde)
        for p in pizzerias:
            n_duenos = random.randint(1, 3)
            duenos_asignados = random.sample(usuarios, n_duenos)
            for d in duenos_asignados:
                # Aquí cambiamos ‘dueño’ → ‘dueno’ y ‘pizzería’ → ‘pizzeria’
                DuenoPizzeria.objects.create(
                    dueno=d,
                    pizzeria=p
                )
            self.stdout.write(f"Asigné {n_duenos} dueño(s) a {p.nombre}")

        # 4) Crear ventas de ejemplo (usar también ‘dueno’ y ‘pizzeria’)
        metodos = ["EFECTIVO", "TARJETA", "OTRO"]
        for p in pizzerias:
            asignaciones = DuenoPizzeria.objects.filter(pizzeria=p)
            for _ in range(random.randint(5, 15)):
                dueno_obj = random.choice(asignaciones).dueno
                dias_aleatorio = random.randint(0, 30)
                horas_aleatorio = random.randint(0, 23)
                minutos_aleatorio = random.randint(0, 59)
                fecha = timezone.now() - timedelta(
                    days=dias_aleatorio,
                    hours=horas_aleatorio,
                    minutes=minutos_aleatorio
                )
                total = round(random.uniform(200.0, 2000.0), 2)
                metodo_pago = random.choice(metodos)

                # Nuevamente, aquí usamos los nombres de campo correctos:
                Venta.objects.create(
                    pizzeria=p,
                    dueno=dueno_obj,
                    fecha=fecha,
                    total=total,
                    metodo_pago=metodo_pago
                )
            self.stdout.write(f"Ventas creadas para {p.nombre}")

        self.stdout.write(self.style.SUCCESS("¡Datos Faker generados correctamente!"))
