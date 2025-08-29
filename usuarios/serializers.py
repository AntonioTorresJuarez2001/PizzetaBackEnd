from rest_framework import serializers
from django.contrib.auth.models import User
from pizzerias.models import Pizzeria
from usuarios.models import (
    UsuarioPizzeriaRol,
    DuenoPizzeria,
    UserProfile,
    TokenNumericoPlano
)

# ————————————————————————————————————————————
# Serializador: UsuarioPizzeriaRol
# ————————————————————————————————————————————
class UsuarioPizzeriaRolSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    pizzeria = serializers.PrimaryKeyRelatedField(queryset=Pizzeria.objects.all())
    user_display = serializers.StringRelatedField(source="user", read_only=True)
    pizzeria_display = serializers.StringRelatedField(source="pizzeria", read_only=True)

    class Meta:
        model = UsuarioPizzeriaRol
        fields = [
            "id", "user", "pizzeria", "rol", "creado",
            "user_display", "pizzeria_display"
        ]

    def validate(self, data):
        user = data.get("user")
        pizzeria = data.get("pizzeria")

        if not self.instance:
            if UsuarioPizzeriaRol.objects.filter(user=user, pizzeria=pizzeria).exists():
                raise serializers.ValidationError("Ese usuario ya tiene un rol en esa pizzería.")
        if self.instance and user != self.instance.user:
            raise serializers.ValidationError("No se puede cambiar el usuario asignado.")
        return data


# ————————————————————————————————————————————
# Serializador: UserProfile
# ————————————————————————————————————————————
class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    username = serializers.StringRelatedField(source="user", read_only=True)

    class Meta:
        model = UserProfile
        fields = ["id", "user", "username", "rol"]


# ————————————————————————————————————————————
# Serializador: TokenNumericoPlano
# ————————————————————————————————————————————
class TokenNumericoPlanoSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    username = serializers.StringRelatedField(source="user", read_only=True)

    class Meta:
        model = TokenNumericoPlano
        fields = ["id", "user", "username", "pin", "creado", "actualizado"]
        read_only_fields = ["creado", "actualizado"]
