from rest_framework import serializers
from .models import Pizzeria


# ————————————————————————————————————————————
# Serializador de Pizzería
# ————————————————————————————————————————————
class PizzeriaSerializer(serializers.ModelSerializer):
    total_ventas = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Pizzeria
        fields = [  # ← esta línea es la que faltaba
            'id',
            'id_local',
            'nombre',
            'direccion',
            'telefono',
            'email',
            'hora_apertura',
            'hora_cierre',
            'total_ventas',
        ]
        extra_kwargs = {
            "nombre": {"required": True},
            "direccion": {"required": False, "allow_null": True, "allow_blank": True},
            "telefono": {"required": False, "allow_null": True, "allow_blank": True},
        }
    
    def create(self, validated_data):
        if 'id_local' not in validated_data or validated_data['id_local'] is None:
            # Evita condiciones de carrera (concurrency)
            from django.db.models import Max
            last_id = Pizzeria.objects.aggregate(Max("id_local"))["id_local__max"] or 0
            validated_data['id_local'] = last_id + 1

        return super().create(validated_data)

    def validate_id_local(self, value):
        # Si estamos actualizando, excluimos esta instancia del filtro
        instance_id = self.instance.id if self.instance else None
        qs = Pizzeria.objects.filter(id_local=value)
        if instance_id:
            qs = qs.exclude(id=instance_id)

        if qs.exists():
            raise serializers.ValidationError("Ya existe una pizzería con este ID Local.")

        return value


