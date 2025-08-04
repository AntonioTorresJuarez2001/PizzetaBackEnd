from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from inventario.models import (
    Pizzeria,
    Insumo,
    MovimientoInventario,
    Receta,
    Ingrediente,
)
from inventario.logic import registrar_salida_por_venta

User = get_user_model()


class InventarioFlowTest(TestCase):

    def setUp(self):
        # Crear una pizzería y usuario
        self.pizzeria = Pizzeria.objects.create(nombre="Pizzería Central")
        self.usuario = User.objects.create_user(username="admin", password="123456")

        # Crear insumos
        self.pan = Insumo.objects.create(
            pizzeria=self.pizzeria,
            nombre="Pan",
            unidad="pieza",
            stock_minimo=2
        )
        self.queso = Insumo.objects.create(
            pizzeria=self.pizzeria,
            nombre="Queso",
            unidad="gramo",
            stock_minimo=100
        )

        # Agregar stock inicial
        MovimientoInventario.objects.create(
            pizzeria=self.pizzeria,
            insumo=self.pan,
            tipo="entrada",
            cantidad=10,
            usuario=self.usuario
        )
        MovimientoInventario.objects.create(
            pizzeria=self.pizzeria,
            insumo=self.queso,
            tipo="entrada",
            cantidad=500,
            usuario=self.usuario
        )

        # Crear producto (solo como ID de referencia)
        from ventas.models import Producto  # Asegúrate que esto exista
        self.producto = Producto.objects.create(
            nombre="Hamburguesa",
            precio=90,
            pizzeria=self.pizzeria
        )

        # Crear receta
        self.receta = Receta.objects.create(
            producto=self.producto,
            pizzeria=self.pizzeria
        )
        Ingrediente.objects.create(receta=self.receta, insumo=self.pan, cantidad=1)
        Ingrediente.objects.create(receta=self.receta, insumo=self.queso, cantidad=50)

    def test_venta_y_descuento(self):
        # Simular una venta de 2 hamburguesas
        registrar_salida_por_venta(
            producto_id=self.producto.id,
            cantidad=2,
            pizzeria_id=self.pizzeria.id,
            usuario_id=self.usuario.id
        )

        # Verificar stock actual
        self.pan.refresh_from_db()
        self.queso.refresh_from_db()

        self.assertEqual(self.pan.stock_actual, 8)     # -2
        self.assertEqual(self.queso.stock_actual, 400) # -100

        # Verificar si hay alerta por stock bajo
        self.assertFalse(self.pan.stock_actual < self.pan.stock_minimo)
        self.assertFalse(self.queso.stock_actual < self.queso.stock_minimo)
