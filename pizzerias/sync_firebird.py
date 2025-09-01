import requests
from datetime import time
from django.utils.dateparse import parse_time
from pizzerias.models import Pizzeria

def parse_safe_time(value):
    if isinstance(value, str) and value.strip():
        try:
            return parse_time(value.strip())
        except ValueError:
            return None
    return None

def clean_text(value):
    if isinstance(value, str):
        return value.strip() or None
    return None

def sincronizar_locales():
    url = "http://localhost:8000/api/firebird/locales/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        locales = response.json()
    except Exception as e:
        print(f"❌ Error al obtener locales: {e}")
        return

    count = 0
    for item in locales:
        try:
            id_local = item.get("id_local")
            if id_local is None:
                print(f"⚠️ Error procesando local: ID inválido (None)")
                continue

            pizzeria_data = {
                "nombre": clean_text(item.get("unidad")),
                "zona": clean_text(item.get("zona")),
                "telefono": clean_text(item.get("tel")),
                "email": clean_text(item.get("email")),
                "hora_apertura": parse_safe_time(item.get("hora_apertura")),
                "hora_cierre": parse_safe_time(item.get("hora_cierre")),
            }

            Pizzeria.objects.update_or_create(
                id_local=id_local,
                defaults=pizzeria_data,
            )
            count += 1
        except Exception as e:
            print(f"⚠️ Error procesando local ID {item.get('id_local')}: {e}")

    print(f"✅ Sincronización completada: {count} pizzerías actualizadas o insertadas.")
