import requests
from productos.models import Producto
from pizzerias.models import Pizzeria

def sincronizar_precios_firebird():
    url_productos = "http://localhost:8000/api/firebird/productos/"
    url_xlocalpro = "http://localhost:8000/api/firebird/xlocal-pro/"
    url_xcrtapro = "http://localhost:8000/api/firebird/xcrta-pro/"

    total_actualizados = 0
    total_creados = 0
    errores = 0

    # 1. Catálogo general de productos
    try:
        response = requests.get(url_productos)
        response.raise_for_status()
        catalogo = response.json()
        catalogo_dict = {
            item["id_pro"]: {
                "nombre": item.get("nombre", f"Producto #{item['id_pro']}"),
                "descripcion": item.get("descripcion", "")
            }
            for item in catalogo
            if "id_pro" in item
        }
    except Exception as e:
        print(f"❌ Error obteniendo catálogo de productos: {e}")
        return

    # 2. Precios y activación desde XcrtaPro
    try:
        response = requests.get(url_xcrtapro)
        response.raise_for_status()
        precios = response.json()
        precios_dict = {
            item["Id_Pro"]: {
                "precio": float(item.get("Precio_Menu") or 0),
                "activo": str(item.get("fActivo", "0")).strip() == "1"
            }
            for item in precios
            if "Id_Pro" in item
        }
    except Exception as e:
        print(f"❌ Error obteniendo precios desde XcrtaPro: {e}")
        return

    # 3. Por cada pizzería, consultar productos disponibles
    for pizzeria in Pizzeria.objects.exclude(id_local__isnull=True):
        try:
            response = requests.get(f"{url_xlocalpro}{pizzeria.id_local}/")
            response.raise_for_status()
            datos = response.json()
        except Exception as e:
            print(f"❌ Error obteniendo datos de local {pizzeria.id_local}: {e}")
            errores += 1
            continue

        for item in datos:
            try:
                id_pro = item["Id_Pro"]
                info = catalogo_dict.get(id_pro)
                pricing = precios_dict.get(id_pro)

                if not info:
                    print(f"⚠️ Producto {id_pro} no está en el catálogo. Ignorado.")
                    continue

                defaults = {
                    "nombre": info["nombre"],
                    "descripcion": info["descripcion"],
                    "precio": pricing["precio"] if pricing else 0,
                    "activo": pricing["activo"] if pricing else False,
                    "categoria": "General",
                }

                producto, creado = Producto.objects.get_or_create(
                    pizzeria=pizzeria,
                    id_externo=id_pro,
                    defaults=defaults
                )

                if creado:
                    total_creados += 1
                    print(f"🆕 Producto creado: {producto.nombre} (local {pizzeria.id_local})")
                else:
                    cambios = []
                    for campo, nuevo_valor in defaults.items():
                        actual_valor = getattr(producto, campo)
                        if actual_valor != nuevo_valor:
                            cambios.append((campo, actual_valor, nuevo_valor))
                            setattr(producto, campo, nuevo_valor)

                    if cambios:
                        producto.save()
                        total_actualizados += 1
                        print(f"🔄 Producto actualizado: {producto.nombre} (local {pizzeria.id_local})")
                        for campo, antes, despues in cambios:
                            print(f"   • {campo}: '{antes}' → '{despues}'")

            except Exception as e:
                print(f"⚠️ Error procesando producto {item.get('Id_Pro')} en local {pizzeria.id_local}: {e}")
                errores += 1

    print("\n  Sincronización finalizada.")
    print(f"   Productos nuevos: {total_creados}")
    print(f"   Productos actualizados: {total_actualizados}")
    print(f"   Errores: {errores}")
