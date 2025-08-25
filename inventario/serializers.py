from rest_framework import serializers
from .models import Insumo, MovimientoInventario, Receta, Ingrediente, FormulaInsumo, FormulaIngrediente, LoteProduccion


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
        
    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault("usuario", request.user)  # ← CLAVE
        obj = MovimientoInventario(**validated_data)
        obj.full_clean()   # valida y normaliza unidades
        obj.save()
        return obj

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.full_clean()
        instance.save()
        return instance


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

# --- Fórmulas (sub-recetas) ---
class FormulaIngredienteSerializer(serializers.ModelSerializer):
    insumo_nombre = serializers.CharField(source='insumo.nombre', read_only=True)

    class Meta:
        model = FormulaIngrediente
        fields = ['id', 'insumo', 'insumo_nombre', 'cantidad', 'unidad']

class FormulaInsumoSerializer(serializers.ModelSerializer):
    insumo_objetivo_nombre = serializers.CharField(source='insumo_objetivo.nombre', read_only=True)
    ingredientes = FormulaIngredienteSerializer(many=True, read_only=True)

    class Meta:
        model = FormulaInsumo
        fields = ['id', 'insumo_objetivo', 'insumo_objetivo_nombre', 'activa',
                  'factor_rendimiento_esperado', 'fecha_creacion', 'ingredientes']

class FormulaInsumoCreateSerializer(serializers.ModelSerializer):
    ingredientes = FormulaIngredienteSerializer(many=True)

    class Meta:
        model = FormulaInsumo
        fields = ['id', 'insumo_objetivo', 'activa', 'factor_rendimiento_esperado', 'ingredientes']

    def create(self, validated_data):
        ingredientes_data = validated_data.pop('ingredientes', [])
        formula = FormulaInsumo.objects.create(**validated_data)
        for ing in ingredientes_data:
            FormulaIngrediente.objects.create(formula=formula, **ing)
        return formula

# --- Lotes de producción ---

class LoteProduccionSerializer(serializers.ModelSerializer):
    insumo_objetivo = serializers.IntegerField(source='formula.insumo_objetivo_id', read_only=True)
    insumo_objetivo_nombre = serializers.CharField(source='formula.insumo_objetivo.nombre', read_only=True)

    class Meta:
        model = LoteProduccion
        fields = [
            'id', 'pizzeria', 'formula', 'usuario',
            'cantidad_objetivo', 'unidad_objetivo',
            'rendimiento_real', 'fecha', 'confirmado',
            'insumo_objetivo', 'insumo_objetivo_nombre'
        ]
        read_only_fields = ['fecha', 'confirmado', 'insumo_objetivo', 'insumo_objetivo_nombre']

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault("usuario", request.user)
        return super().create(validated_data)
