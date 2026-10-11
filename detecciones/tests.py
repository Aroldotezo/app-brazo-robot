import io
import base64
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.management import call_command
from channels.testing import WebsocketCommunicator

from config.asgi import application
from detecciones.models import Deteccion

User = get_user_model()


class AuthenticationAndLandingTests(TestCase):
    """
    Test suite for user model, bcrypt password hasher, views, and authentication flow.
    """

    def setUp(self):
        self.client = Client()
        call_command('seed_users')

    def test_seed_users_created_with_bcrypt(self):
        """Verify seeded users exist with correct roles, phones, and bcrypt hashes."""
        lolo = User.objects.get(username='lolo')
        pablito = User.objects.get(username='pablito')

        self.assertEqual(lolo.first_name, 'Lolo')
        self.assertEqual(lolo.phone, '123456789')
        self.assertEqual(lolo.role, 'admin')
        self.assertTrue(lolo.is_admin())
        self.assertTrue(lolo.password.startswith('bcrypt'))

        self.assertEqual(pablito.first_name, 'Pablito')
        self.assertEqual(pablito.phone, '987654321')
        self.assertEqual(pablito.role, 'operator')
        self.assertTrue(pablito.is_operator())
        self.assertTrue(pablito.password.startswith('bcrypt'))

    def test_landing_page_renders_for_unauthenticated_user(self):
        """Verify landing page at '/' is accessible and contains 'Iniciar Sesión'."""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar Sesión')
        self.assertContains(response, 'Brazo Robot')
        self.assertContains(response, 'Clasificación')

    def test_dashboard_requires_login(self):
        """Verify accessing /dashboard/ without login redirects to /login/."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_login_with_invalid_credentials(self):
        """Verify login failure renders error message in Spanish."""
        response = self.client.post(reverse('login'), {
            'username': 'lolo',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos')

    def test_login_successful_and_redirects_to_dashboard(self):
        """Verify valid login authenticates user and redirects to /dashboard/."""
        response = self.client.post(reverse('login'), {
            'username': 'lolo',
            'password': 'admin123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lolo')
        self.assertContains(response, 'Cerrar Sesión')
        self.assertContains(response, 'Monitoreo de Residuos')

    def test_logout_redirects_to_landing_page(self):
        """Verify logout view logs user out and redirects to landing page."""
        self.client.login(username='pablito', password='admin123')
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar Sesión')


class DetectionApiAndWebSocketTests(TestCase):
    """
    Test suite for REST API endpoint and WebSocket camera streaming consumer.
    """

    def setUp(self):
        self.client = Client()
        call_command('seed_users')

    def _generate_test_image(self):
        """Helper generating a small in-memory JPEG test image."""
        img = Image.new('RGB', (64, 64), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        return SimpleUploadedFile("test_capture.jpg", buffer.read(), content_type="image/jpeg")

    def test_api_create_detection_without_image(self):
        """Verify POST /api/detecciones/ creates record and normalizes confidence."""
        payload = {
            'objeto': 'botella_pet',
            'categoria': 'inorganico',
            'confianza': 95.5,
            'camara_id': 'CAM_01',
        }
        response = self.client.post('/api/detecciones/', payload)
        self.assertEqual(response.status_code, 201)

        detection = Deteccion.objects.get(id=response.data['id'])
        self.assertEqual(detection.objeto, 'botella_pet')
        self.assertEqual(detection.categoria, 'inorganico')
        self.assertAlmostEqual(detection.confianza, 0.955, places=3)
        self.assertEqual(detection.camara_id, 'CAM_01')

    def test_api_create_detection_with_image(self):
        """Verify POST /api/detecciones/ saves uploaded image to capturas directory."""
        test_file = self._generate_test_image()
        payload = {
            'objeto': 'manzana',
            'categoria': 'organico',
            'confianza': 0.92,
            'camara_id': 'CAM_01',
            'imagen': test_file,
        }
        response = self.client.post('/api/detecciones/', payload, format='multipart')
        self.assertEqual(response.status_code, 201)

        detection = Deteccion.objects.get(id=response.data['id'])
        self.assertTrue(bool(detection.imagen))
        self.assertTrue(detection.imagen.name.startswith('capturas/'))

    async def test_websocket_camera_stream_consumer_connection_and_ping(self):
        """Verify WebSocket connection, handshake, and ping/pong heartbeat."""
        communicator = WebsocketCommunicator(application, "/ws/camera/CAM_01/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Receive connection established message
        response = await communicator.receive_json_from()
        self.assertEqual(response.get('type'), 'connection_established')
        self.assertEqual(response.get('camera_id'), 'CAM_01')

        # Send ping and receive pong
        await communicator.send_json_to({'type': 'ping'})
        pong = await communicator.receive_json_from()
        self.assertEqual(pong.get('type'), 'pong')

        await communicator.disconnect()

    def test_api_create_detection_with_json_base64_image(self):
        """Verify POST /api/detecciones/ handles base64 image strings in JSON payload."""
        img = Image.new('RGB', (32, 32), color='green')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{b64_str}"

        payload = {
            'objeto': 'Lata de refresco',
            'categoria': 'Inorgánico',
            'confianza': 0.97,
            'camara_id': 'CAM_01',
            'imagen': data_uri,
        }
        response = self.client.post('/api/detecciones/', payload, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        det = Deteccion.objects.get(id=response.data['id'])
        self.assertEqual(det.objeto, 'Lata de refresco')
        self.assertEqual(det.categoria, 'Inorgánico')
        self.assertTrue(bool(det.imagen))
        self.assertTrue(det.imagen.name.startswith('capturas/'))

    def test_api_list_detections(self):
        """Verify GET /api/detecciones/ returns detection records ordered by recent."""
        Deteccion.objects.create(objeto='Item 1', categoria='Orgánico', confianza=0.88, camara_id='CAM_01')
        Deteccion.objects.create(objeto='Item 2', categoria='Inorgánico', confianza=0.94, camara_id='CAM_01')

        response = self.client.get('/api/detecciones/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 2)

    def test_dashboard_displays_detections_and_sin_foto_fallback(self):
        """Verify dashboard table renders detections and 'Sin foto' fallback when image is None."""
        user = User.objects.get(username='lolo')
        self.client.force_login(user)

        # Detection without image
        Deteccion.objects.create(
            objeto='Cáscara de Plátano Test',
            categoria='Orgánico',
            confianza=0.91,
            camara_id='CAM_01',
            imagen=None
        )

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cáscara de Plátano Test')
        self.assertContains(response, 'Orgánico')
        self.assertContains(response, 'Sin foto')
        self.assertContains(response, 'Cámara / Ubicación')

    def test_seed_detections_command(self):
        """Verify python manage.py seed_detections successfully creates sample records."""
        call_command('seed_detections', clear=True)
        self.assertGreaterEqual(Deteccion.objects.count(), 8)
        self.assertTrue(Deteccion.objects.filter(objeto__icontains='Botella').exists())
        self.assertTrue(Deteccion.objects.filter(objeto__icontains='Manzana').exists())
