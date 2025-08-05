from rest_framework import serializers
from .models import Insumo, MovimientoInventario, Receta, Ingrediente


class InsumoSerializer(serializers.ModelSerializer):
    stock_actual = serializers.FloatField(read_only=True)

    class Meta:
        model = Insumo
        fields = '__all__'


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    insumo_nombre = serializers.CharField(source='insumo.nombre', read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = '__all__'


class IngredienteSerializer(serializers.ModelSerializer):
    insumo_nombre = serializers.CharField(source='insumo.nombre', read_only=True)

    class Meta:
        model = Ingrediente
        fields = ['id', 'insumo', 'insumo_nombre', 'cantidad', 'unidad']


class RecetaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    ingredientes = IngredienteSerializer(many=True, read_only=True)

    class Meta:
        model = Receta
        fields = ['id', 'producto', 'producto_nombre', 'activa', 'fecha_creacion', 'ingredientes']


# Para crear receta con ingredientes en un solo request
class RecetaConIngredientesSerializer(serializers.ModelSerializer):
    ingredientes = IngredienteSerializer(many=True)

    class Meta:
        model = Receta
        fields = ['id', 'producto', 'activa', 'ingredientes']

    def create(self, validated_data):
        ingredientes_data = validated_data.pop('ingredientes')
        receta = Receta.objects.create(**validated_data)
        for ingrediente in ingredientes_data:
            Ingrediente.objects.create(receta=receta, **ingrediente)
        return receta
