# ventas/management/commands/borrar_ventas_miyana.py

from django.core.management.base import BaseCommand
from ventas.models import Pizzeria, Venta

class Command(BaseCommand):
    help = "Borra todas las ventas asociadas a Pizzería Miyana"

    def handle(self, *args, **options):
        nombre_objetivo = "Pizzería Miyana"

        try:
            pizzeria = Pizzeria.objects.get(nombre=nombre_objetivo)
        except Pizzeria.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"No existe la Pizzería con nombre '{nombre_objetivo}'."
            ))
            return

        # Filtrar y eliminar
        cantidad, _ = Venta.objects.filter(pizzeria=pizzeria).delete()
        self.stdout.write(self.style.SUCCESS(
            f"Se eliminaron {cantidad} venta(s) de '{nombre_objetivo}'."
        ))
