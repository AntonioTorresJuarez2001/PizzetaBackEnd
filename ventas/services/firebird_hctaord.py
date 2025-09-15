# ventas/services/firebird_hctaord.py
import requests
from django.conf import settings

API_BASE = getattr(settings, "FIREBIRD_API_BASE", "http://localhost:8000/api/firebird")

def get_hctaord(id_local=None, fecha=None, id_cta=None, params=None, timeout=10):
    """
    Llama al endpoint Hctaord del proyecto Firebird.
    - Si vienen id_local+fecha+id_cta => usa la ruta específica /.../{id_local}/{fecha}/{id_cta}/
    - Si no, usa listado general con filtros via query params.
    """
    if not API_BASE:
        raise RuntimeError("FIREBIRD_API_BASE no está configurado en settings.")

    url = f"{API_BASE}/hctaord/"
    if id_local and fecha and id_cta:
        url = f"{url}{id_local}/{fecha}/{id_cta}/"

    r = requests.get(url, params=params, timeout=30)

    r.raise_for_status()
    return r.json()

def get_producto_firebird(id_pro):
    """
    Consulta producto en Firebird por Id_Pro.
    Usa el endpoint /productos/<id_pro>/ ya implementado en Firebird.
    """
    if not API_BASE:
        raise RuntimeError("FIREBIRD_API_BASE no está configurado en settings.")

    url = f"{API_BASE}/productos/{id_pro}/"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()