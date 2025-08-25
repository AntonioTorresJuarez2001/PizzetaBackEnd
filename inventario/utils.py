# inventario/utils.py
from django.core.exceptions import ValidationError

UNIT_FACTORS = {
    ("gramo", "kilogramo"): 0.001,
    ("kilogramo", "gramo"): 1000.0,
    ("mililitro", "litro"): 0.001,
    ("litro", "mililitro"): 1000.0,
    # 'pieza' no convierte con peso/volumen
}

# 👇 NUEVO: alias y normalización
UNIT_ALIASES = {
    "kg": "kilogramo", "kilo": "kilogramo", "kilogramos": "kilogramo",
    "g": "gramo", "gr": "gramo", "gramos": "gramo",
    "l": "litro", "lt": "litro", "litros": "litro",
    "ml": "mililitro", "millilitro": "mililitro", "mililitros": "mililitro",
    "pz": "pieza", "pza": "pieza", "piezas": "pieza",
}

def _normalize_unit(u: str) -> str:
    u = (u or "").strip().lower()
    return UNIT_ALIASES.get(u, u)

def convert_qty(qty: float, from_unit: str, to_unit: str) -> float:
    # 👇 normaliza SIEMPRE
    from_unit = _normalize_unit(from_unit)
    to_unit   = _normalize_unit(to_unit)

    if from_unit == to_unit:
        return qty
    if from_unit == "pieza" or to_unit == "pieza":
        raise ValidationError("No es posible convertir entre 'pieza' y unidades de peso/volumen.")
    factor = UNIT_FACTORS.get((from_unit, to_unit))
    if factor is None:
        raise ValidationError(f"Conversión no soportada: {from_unit} → {to_unit}.")
    return qty * factor
