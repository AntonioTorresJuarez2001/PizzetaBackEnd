# ventas/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'perfil'):
        UserProfile.objects.create(user=instance)

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import UsuarioPizzeriaRol, UserProfile

@receiver(post_save, sender=UsuarioPizzeriaRol)
def actualizar_rol_global_al_guardar(sender, instance, **kwargs):
    """Cuando se asigna/modifica un rol en una pizzería, se actualiza el perfil global."""
    try:
        perfil = UserProfile.objects.get(user=instance.user)
        perfil.rol = instance.rol
        perfil.save()
    except UserProfile.DoesNotExist:
        pass

@receiver(post_delete, sender=UsuarioPizzeriaRol)
def actualizar_rol_global_al_eliminar(sender, instance, **kwargs):
    """Cuando se elimina un rol, se revisa si el usuario aún tiene otro rol en otra pizzería."""
    try:
        perfil = UserProfile.objects.get(user=instance.user)
        otras_asignaciones = UsuarioPizzeriaRol.objects.filter(user=instance.user)

        if otras_asignaciones.exists():
            # Asignamos el rol de la primera asignación restante
            perfil.rol = otras_asignaciones.first().rol
        else:
            # Si ya no tiene asignaciones, se asigna un rol neutral
            perfil.rol = "empleado"  # o "sin_rol", si defines esa opción
        perfil.save()
    except UserProfile.DoesNotExist:
        pass
