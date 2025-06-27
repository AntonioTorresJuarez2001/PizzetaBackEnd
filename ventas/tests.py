from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from ventas.models import Pizzeria, Producto, Venta, DuenoPizzeria
from faker import Faker

fake = Faker()

class APITestSuite(APITestCase):
    def setUp(self):
        # Crear usuario y autenticación
        self.user = User.objects.create_user(
            username=fake.user_name(), password="testpass123"
        )
        self.client = APIClient()
        token_url = reverse('token_obtain_pair')
        response = self.client.post(
            token_url,
            {'username': self.user.username, 'password': 'testpass123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_crud_completo(self):
        # Crear pizzería
        pizzeria_data = {'nombre': fake.company(), 'direccion': fake.address(), 'telefono': fake.phone_number()}
        res = self.client.post(reverse('lista-pizzerias'), pizzeria_data, format='json')
        self.assertEqual(res.status_code, 201)
        pizzeria_id = res.data['id']

        # Ver listado
        res = self.client.get(reverse('lista-pizzerias'))
        self.assertEqual(res.status_code, 200)

        # Crear producto
        producto_data = {
            'nombre': fake.word(),
            'precio': '100.50',
            'categoria': 'Test',
            'descripcion': fake.sentence(),
            'activo': True
        }
        productos_url = reverse('productos-por-pizzeria', kwargs={'pizzeria_id': pizzeria_id})
        res = self.client.post(productos_url, producto_data, format='json')
        self.assertEqual(res.status_code, 201)
        producto_id = res.data['id']

        # Crear venta
        ventas_url = reverse('ventas-list-create', kwargs={'pizzeria_id': pizzeria_id})
        venta_payload = {
            'canal': 'MOSTRADOR',
            'metodo_pago': 'EFECTIVO',
            'items': [
                {'producto': producto_id, 'cantidad': 2},
                {'producto': producto_id, 'cantidad': 1}
            ]
        }
        res = self.client.post(ventas_url, venta_payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(float(res.data['total']), 100.50 * 3)
        venta_id = res.data['id']

        # Resumen
        res = self.client.get(f"{reverse('resumen-ventas')}?rango=ayer")
        self.assertEqual(res.status_code, 200)
        self.assertIn('total', res.data)

        # Editar producto
        prod_detail = reverse('producto-detail-by-pizzeria', kwargs={'pizzeria_id': pizzeria_id, 'pk': producto_id})
        res = self.client.put(prod_detail, {**producto_data, 'nombre': 'Updated'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['nombre'], 'Updated')

        # Eliminar venta, producto y pizzería
        venta_detail = reverse('venta-detail-by-pizzeria', kwargs={'pizzeria_id': pizzeria_id, 'venta_id': venta_id})
        self.assertEqual(self.client.delete(venta_detail).status_code, 204)
        self.assertEqual(self.client.delete(prod_detail).status_code, 204)
        pizzeria_detail = reverse('detalle-pizzeria', kwargs={'pizzeria_id': pizzeria_id})
        self.assertEqual(self.client.delete(pizzeria_detail).status_code, 204)

    def test_venta_con_producto_inactivo(self):
        p = Pizzeria.objects.create(nombre="Inactiva")
        DuenoPizzeria.objects.create(dueno=self.user, pizzeria=p)
        producto = Producto.objects.create(pizzeria=p, nombre="Inactivo", precio=50, categoria="Pizza", activo=False)
        payload = {
            'canal': 'LLEVAR',
            'metodo_pago': 'TARJETA',
            'items': [{'producto': producto.id, 'cantidad': 1}]
        }
        res = self.client.post(reverse('ventas-list-create', kwargs={'pizzeria_id': p.id}), payload, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("no está activo", str(res.data))

    def test_venta_con_cantidad_negativa(self):
        p = Pizzeria.objects.create(nombre="CantidadNegativa")
        DuenoPizzeria.objects.create(dueno=self.user, pizzeria=p)
        producto = Producto.objects.create(pizzeria=p, nombre="Coca", precio=25, categoria="Bebida", activo=True)
        payload = {
            'canal': 'DOMICILIO',
            'metodo_pago': 'EFECTIVO',
            'items': [{'producto': producto.id, 'cantidad': -2}]
        }
        res = self.client.post(reverse('ventas-list-create', kwargs={'pizzeria_id': p.id}), payload, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("cantidad", res.data["items"][0])


    def test_resumen_con_rango_personalizado(self):
        p = Pizzeria.objects.create(nombre="ResumenManual")
        DuenoPizzeria.objects.create(dueno=self.user, pizzeria=p)
        Producto.objects.create(pizzeria=p, nombre="Pizza", precio=100, categoria="Comida", activo=True)
        Venta.objects.create(pizzeria=p, dueno=self.user, total=150, canal="MOSTRADOR", metodo_pago="EFECTIVO")
        url = f"{reverse('resumen-ventas')}?rango=personalizado&inicio=2020-01-01&fin=2030-01-01"
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertGreater(float(res.data["total"]), 0)

    def test_resumen_con_fecha_invalida(self):
        url = f"{reverse('resumen-ventas')}?rango=personalizado&inicio=2020-01&fin=2030"
        res = self.client.get(url)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Fechas inválidas", str(res.data))

    def test_venta_sin_autenticacion(self):
        self.client.credentials()  # elimina el token
        res = self.client.get(reverse('lista-pizzerias'))
        self.assertEqual(res.status_code, 401)
