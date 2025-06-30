from django.core.management.base import BaseCommand
from ventas.models import Producto, Pizzeria, DuenoPizzeria
from faker import Faker
import random
from django.contrib.auth.models import User

fake = Faker()

# Diccionario de categorías con ejemplos reales
PRODUCTOS_PIZZERIA = {
    'Pizza': [
        'Pizza Pepperoni', 'Pizza Hawaiana', 'Pizza 4 Quesos', 'Pizza Mexicana',
        'Pizza Vegetariana', 'Pizza BBQ Pollo', 'Pizza Margarita'
    ],
    'Bebida': [
        'Coca-Cola 600ml', 'Agua Natural', 'Sprite 355ml', 'Fanta Naranja',
        'Jugo de Mango', 'Cerveza Artesanal', 'Té Helado'
    ],
    'Postre': [
        'Cheesecake', 'Brownie con helado', 'Flan Napolitano', 'Gelatina de mosaico',
        'Churros rellenos', 'Tarta de limón', 'Panqué de plátano'
    ],
    'Entrada': [
        'Pan de ajo', 'Alitas BBQ', 'Dedos de queso', 'Nachos con queso',
        'Ensalada César', 'Papas gajo', 'Bruschettas'
    ],
    'Complemento': [
        'Extra queso', 'Aderezo ranch', 'Salsa picante', 'Orilla rellena',
        'Salsa BBQ', 'Mayonesa chipotle', 'Tortillas adicionales'
    ]
}

class Command(BaseCommand):
    help = "Genera productos relacionados con comida para pizzerías de un usuario"

    def add_arguments(self, parser):
        parser.add_argument('--usuario', type=str, required=True, help='Nombre de usuario del dueño')
        parser.add_argument('--cantidad', type=int, default=10, help='Número de productos a crear por pizzería')

    def handle(self, *args, **options):
        username = options['usuario']
        cantidad = options['cantidad']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Usuario '{username}' no encontrado"))
            return

        pizzerias = Pizzeria.objects.filter(dueno_asignaciones__dueno=user)
        if not pizzerias.exists():
            self.stderr.write(self.style.ERROR(f"No hay pizzerías asignadas a '{username}'"))
            return

        for pizzeria in pizzerias:
            for _ in range(cantidad):
                categoria = random.choice(list(PRODUCTOS_PIZZERIA.keys()))
                nombre = random.choice(PRODUCTOS_PIZZERIA[categoria])

                Producto.objects.create(
                    pizzeria=pizzeria,
                    nombre=nombre,
                    precio=round(random.uniform(40, 200), 2),
                    categoria=categoria,
                    descripcion=fake.text(max_nb_chars=60),
                    activo=random.choice([True, True, True, False])  # mayoría activos
                )

            self.stdout.write(self.style.SUCCESS(
                f"{cantidad} productos generados para pizzería '{pizzeria.nombre}'"
            ))

        self.stdout.write(self.style.SUCCESS("✅ Generación de productos de pizzería completada"))
