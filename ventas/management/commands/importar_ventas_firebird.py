from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.conf import settings
from productos.models import Producto
from pizzerias.models import Pizzeria
from ventas.models import Venta, VentaProducto, VentaEtapa
from ventas.services.firebird_hctaord import get_hctaord
from django.db import transaction
from datetime import datetime, timedelta
import requests
from collections import defaultdict
import time
from django.contrib.auth import get_user_model
User = get_user_model()


class Command(BaseCommand):
    help = "Importa todas las ventas históricas desde la tabla Hctaord (Firebird)"

    def add_arguments(self, parser):
        parser.add_argument("--id-local", type=int, required=True, help="ID del local Firebird")
        parser.add_argument("--crear-productos", action="store_true", help="Crear productos si no existen")
        parser.add_argument("--dry-run", action="store_true", help="Simular sin guardar en la base de datos")
        parser.add_argument( "--limite-registros",type=int,help="Número máximo de registros totales a importar desde Firebird (últimos N registros)")
        
        parser.add_argument("--desde", type=int, help="Fecha Firebird inicial (como número, ej. 45100)")
        parser.add_argument("--hasta", type=int, help="Fecha Firebird final (como número, ej. 45900)")

    def handle(self, *args, **options):
        id_local = options["id_local"]
        crear_productos = options["crear_productos"]
        dry_run = options["dry_run"]
        limite = options.get("limite_registros")
        ventas_procesadas = 0

        print(f"\n🚀 Iniciando importación total de ventas desde Firebird (local={id_local})\n")

        try:
            pizzeria = Pizzeria.objects.get(id_local=id_local)
        except Pizzeria.DoesNotExist:
            self.stderr.write(f"❌ No se encontró una pizzería con id_local={id_local}")
            return

        # 🔍 Detectar primera fecha disponible
        try:
            API_BASE = getattr(settings, "FIREBIRD_API_BASE", "http://localhost:8000/api/firebird")
            response = requests.get(f"{API_BASE}/hctaord/", params={"id_local": id_local}, timeout=60000)
            response.raise_for_status()
            registros = response.json()
        except Exception as e:
            self.stderr.write(f"❌ Error al consultar registros base: {e}")
            return

        if not registros:
            self.stderr.write("⚠️ No hay registros en Hctaord para este local.")
            return

        fechas = [r["Fecha"] for r in registros if "Fecha" in r]
        hoy = now().date()
        base_date = datetime(1899, 12, 30)
        fecha_min = options["desde"] if options["desde"] else min(fechas)
        fecha_max = options["hasta"] if options["hasta"] else (hoy - base_date.date()).days

        print(f"📅 Rango detectado: {fecha_min} → {fecha_max}\n")

        importadas = 0
        existentes = 0
        con_errores = 0
        productos_creados = 0

        for fecha in range(fecha_min, fecha_max + 1):
            print(f"📆 Procesando fecha Firebird {fecha}...")
            try:
                registros = get_hctaord(params={"id_local": id_local, "fecha_ini": fecha, "fecha_fin": fecha})
            except Exception as e:
                self.stderr.write(f"⚠️ Error al consultar fecha {fecha}: {e}")
                continue

            cuentas = defaultdict(list)
            for r in registros:
                key = (r["Id_Cta"], r["Fecha"])
                cuentas[key].append(r)

            for (id_cta, fecha_fbd), items in cuentas.items():
                if limite and ventas_procesadas >= limite:
                    print(f"🛑 Límite de {limite} ventas alcanzado.")
                    break

                id_ord = items[0].get("Id_Ord", 1)
                folio = f"{fecha_fbd}{id_local}{id_cta}"

                if Venta.objects.filter(pizzeria=pizzeria, folio_ticket=folio).exists():
                    existentes += 1
                    continue

                faltantes = []
                for r in items:
                    if not Producto.objects.filter(pizzeria=pizzeria, id_externo=r["Id_Pro"]).exists():
                        faltantes.append(r)

                if faltantes and not crear_productos:
                    con_errores += 1
                    self.stdout.write(f"⛔ Saltando venta {folio} (productos faltantes)")
                    continue

                if dry_run:
                    self.stdout.write(f"Simulando importación de venta {folio}")
                    importadas += 1
                    ventas_procesadas += 1
                    continue

                # Crear venta real
                with transaction.atomic():
                    dueno = User.objects.filter(username="admin").first()

                    total = sum(r.get("M_Total") or 0 for r in items)

                    # Convertir fecha Firebird a datetime real
                    fecha_real = base_date + timedelta(days=fecha_fbd)

                    venta = Venta.objects.create(
                        pizzeria=pizzeria,
                        dueno=dueno,
                        fecha=fecha_real,
                        canal="MOSTRADOR",
                        metodo_pago="EFECTIVO",
                        folio_ticket=folio,
                        total=total
                    )

                    for r in items:
                        id_pro = r["Id_Pro"]
                        nombre = r.get("Producto", f"Producto {id_pro}")
                        precio = r.get("Precio_Unit") or 0
                        categoria = r.get("Linea") or "Firebird"

                        producto, creado = Producto.objects.get_or_create(
                            pizzeria=pizzeria,
                            id_externo=id_pro,
                            defaults={
                                "nombre": nombre,
                                "precio": precio,
                                "categoria": categoria,
                                "activo": True,
                                "descripcion": nombre,
                            }
                        )

                        if creado:
                            productos_creados += 1

                        VentaProducto.objects.create(
                            venta=venta,
                            producto=producto,
                            cantidad=int(r.get("Porciones") or 1)
                        )

                    VentaEtapa.objects.create(
                        venta=venta,
                        etapa="toma_pedido_inicio",
                        timestamp=now()
                    )

                    self.stdout.write(f"✅ Venta importada: {folio}")
                    importadas += 1
                    ventas_procesadas += 1

            if limite and ventas_procesadas >= limite:
                break

            time.sleep(0.25)

        print("\n📊 RESUMEN FINAL")
        print(f"✅ Ventas importadas:   {importadas}")
        print(f"📁 Ventas ya existentes:{existentes}")
        print(f"⛔ Ventas con errores:  {con_errores}")
        print(f"📦 Productos creados:   {productos_creados}")
        print(f"🧪 Modo simulación:     {'Sí' if dry_run else 'No'}")
