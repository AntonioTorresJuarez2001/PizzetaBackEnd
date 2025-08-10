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
            'id',
            'nombre',
            'precio',
            'categoria',
            'descripcion',
            'activo',
            'pizzeria',
            'created_at',
        ]
        extra_kwargs = {
            'categoria': {'required': True, 'allow_blank': False},
            'descripcion': {'required': False, 'allow_blank': True},
            'activo': {'required': True},
            'precio': {'min_value': 0}

        }
    
    def validate_nombre(self, value: str):
        """
        Evita duplicados de nombre dentro de la misma pizzería.
        Usa pizzeria_id de la URL (view.kwargs) porque el campo es read_only.
        """
        view = self.context.get("view")
        pizzeria_id = getattr(view, "kwargs", {}).get("pizzeria_id")

        # Si por alguna razón no hay pizzeria_id (ej. schema), no validamos aquí.
        if not pizzeria_id:
            return value

        qs = Producto.objects.filter(
            pizzeria_id=pizzeria_id,
            nombre__iexact=value.strip()  # case-insensitive
        )
        # En update, excluye el propio registro
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ya existe un producto con ese nombre en esta unidad."
            )
        return value

