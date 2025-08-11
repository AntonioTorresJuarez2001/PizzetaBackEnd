# inventario/utils.py
from django.core.exceptions import ValidationError

UNIT_FACTORS = {
    ("gramo", "kilogramo"): 0.001,
    ("kilogramo", "gramo"): 1000.0,
    ("mililitro", "litro"): 0.001,
    ("litro", "mililitro"): 1000.0,
    # 'pieza' no convierte con peso/volumen
}

def convert_qty(qty: float, from_unit: str, to_unit: str) -> float:
    if from_unit == to_unit:
        return qty
    if from_unit == "pieza" or to_unit == "pieza":
        raise ValidationError("No es posible convertir entre 'pieza' y unidades de peso/volumen.")
    factor = UNIT_FACTORS.get((from_unit, to_unit))
    if factor is None:
        raise ValidationError(f"Conversión no soportada: {from_unit} → {to_unit}.")
    return qty * factor
