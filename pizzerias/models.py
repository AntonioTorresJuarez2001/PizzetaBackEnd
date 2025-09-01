from django.db import models

class Pizzeria(models.Model):
    id_local = models.IntegerField(unique=True)  # identificador Firebird
    nombre      = models.CharField(max_length=100)
    direccion   = models.CharField(max_length=200, blank=True, null=True)
    zona = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    hora_apertura = models.TimeField(null=True, blank=True)
    hora_cierre = models.TimeField(null=True, blank=True)
    telefono    = models.CharField(max_length=20,  blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pizzeria"
        verbose_name = "Pizzería"
        verbose_name_plural = "Pizzerías"

    def __str__(self):
        return self.nombre
