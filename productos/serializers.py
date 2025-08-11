from productos.models import Producto
from rest_framework import serializers


# ————————————————————————————————————————————
# Serializador de Producto
# ————————————————————————————————————————————
class ProductoSerializer(serializers.ModelSerializer):
    pizzeria = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id",           # PK interno
            "id_externo",   # Id_Pro del cliente (opcional)
            "nombre",
            "precio",
            "categoria",
            "descripcion",
            "activo",
            "pizzeria",
            "created_at",
        ]
        extra_kwargs = {
            # ← ya NO es requerido y acepta null
            "id_externo": {"required": False, "allow_null": True},
            "categoria": {"required": True, "allow_blank": False},
            "descripcion": {"required": False, "allow_blank": True},
            "activo": {"required": True},
            "precio": {"min_value": 0},
        }

    def _get_pizzeria_id(self):
        view = self.context.get("view")
        return getattr(view, "kwargs", {}).get("pizzeria_id")

    def validate_id_externo(self, value):
        """
        Reglas:
        - Permite null (producto propio).
        - Si viene con valor, debe ser entero positivo y único en la pizzería.
        """
        # Normaliza "" -> None (por si el front manda string vacío)
        if value in ("", None):
            return None

        # Acepta ints o strings numéricos
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError("id_externo debe ser un entero positivo.")

        if value <= 0:
            raise serializers.ValidationError("id_externo debe ser un entero positivo.")

        pizzeria_id = self._get_pizzeria_id()
        if not pizzeria_id:
            return value  # en generación de schema/otros contextos

        qs = Producto.objects.filter(pizzeria_id=pizzeria_id, id_externo=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ya existe un producto con ese id_externo en esta unidad."
            )
        return value

    def validate_nombre(self, value: str):
        """
        Evita duplicados de nombre dentro de la misma pizzería (case-insensitive).
        """
        pizzeria_id = self._get_pizzeria_id()
        if not pizzeria_id:
            return value

        nombre = (value or "").strip()
        qs = Producto.objects.filter(pizzeria_id=pizzeria_id, nombre__iexact=nombre)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ya existe un producto con ese nombre en esta unidad."
            )
        return nombre

    def to_internal_value(self, data):
        """
        Convierte id_externo "" -> None antes de validar tipos.
        """
        mutable = dict(data)
        if "id_externo" in mutable and mutable["id_externo"] == "":
            mutable["id_externo"] = None
        return super().to_internal_value(mutable)