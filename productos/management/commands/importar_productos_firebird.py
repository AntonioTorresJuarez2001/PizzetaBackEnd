# productos/management/commands/importar_productos_firebird.py

import requests
from django.core.management.base import BaseCommand
from productos.models import Producto
from ventas.models import Pizzeria

FIREBIRD_API_URL = "http://localhost:8000/api/firebird/productos/"

class Command(BaseCommand):
    help = "Importa productos desde el catálogo Firebird de Martin"

    def handle(self, *args, **kwargs):
        try:
            response = requests.get(FIREBIRD_API_URL, timeout=10)
            response.raise_for_status()
            productos_firebird = response.json()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error al consumir la API: {e}"))
            return

        pizzeria_general = Pizzeria.objects.order_by("id").first()
        if not pizzeria_general:
            self.stderr.write(self.style.ERROR("❌ No hay pizzerías registradas"))
            return

        nuevos, actualizados = 0, 0

        for p in productos_firebird:
            id_externo = p.get("id_pro")
            nombre = p.get("nombre") or f"Producto {id_externo}"  # Nombre por defecto si viene None
            descripcion = p.get("descripcion") or ""

            try:
                obj, creado = Producto.objects.update_or_create(
                    pizzeria=pizzeria_general,
                    id_externo=id_externo,
                    defaults={
                        "nombre": nombre,
                        "descripcion": descripcion,
                        "categoria": "General",
                        "precio": 0,
                        "activo": True
                    }
                )
                if creado:
                    nuevos += 1
                else:
                    actualizados += 1
            except Exception as e:
                self.stderr.write(f"❌ Error con producto {p}: {e}")


        self.stdout.write(self.style.SUCCESS(f"✅ Productos sincronizados: {nuevos} nuevos, {actualizados} actualizados."))
