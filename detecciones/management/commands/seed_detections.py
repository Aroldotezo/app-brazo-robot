import io
from PIL import Image, ImageDraw
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from detecciones.models import Deteccion


class Command(BaseCommand):
    help = "Seed database with sample waste detection records for dashboard and API testing"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing detection records before seeding',
        )

    def _create_sample_image(self, color=(37, 99, 235), label="DET"):
        """Generate a small thumbnail image in memory."""
        img = Image.new('RGB', (120, 120), color=color)
        draw = ImageDraw.Draw(img)
        draw.rectangle([(10, 10), (110, 110)], outline=(255, 255, 255), width=2)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        return ContentFile(buffer.read())

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count, _ = Deteccion.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} existing detection records."))

        sample_items = [
            {
                'objeto': 'Botella de plástico (PET)',
                'categoria': 'Inorgánico',
                'confianza': 0.96,
                'camara_id': 'CAM_01',
                'with_image': True,
                'color': (59, 130, 246),
            },
            {
                'objeto': 'Cáscara de plátano',
                'categoria': 'Orgánico',
                'confianza': 0.94,
                'camara_id': 'CAM_01',
                'with_image': True,
                'color': (16, 185, 129),
            },
            {
                'objeto': 'Lata de aluminio',
                'categoria': 'Inorgánico',
                'confianza': 0.98,
                'camara_id': 'CAM_01',
                'with_image': True,
                'color': (245, 158, 11),
            },
            {
                'objeto': 'Manzana',
                'categoria': 'Orgánico',
                'confianza': 0.91,
                'camara_id': 'CAM_01',
                'with_image': False,
            },
            {
                'objeto': 'Vaso desechable',
                'categoria': 'Inorgánico',
                'confianza': 0.89,
                'camara_id': 'CAM_01',
                'with_image': True,
                'color': (99, 102, 241),
            },
            {
                'objeto': 'Restos de verdura',
                'categoria': 'Orgánico',
                'confianza': 0.93,
                'camara_id': 'CAM_01',
                'with_image': False,
            },
            {
                'objeto': 'Caja de cartón',
                'categoria': 'Inorgánico',
                'confianza': 0.97,
                'camara_id': 'CAM_01',
                'with_image': True,
                'color': (217, 119, 6),
            },
            {
                'objeto': 'Cáscara de naranja',
                'categoria': 'Orgánico',
                'confianza': 0.88,
                'camara_id': 'CAM_01',
                'with_image': False,
            },
        ]

        created_count = 0
        for item in sample_items:
            det = Deteccion(
                objeto=item['objeto'],
                categoria=item['categoria'],
                confianza=item['confianza'],
                camara_id=item['camara_id'],
            )
            if item.get('with_image'):
                image_file = self._create_sample_image(
                    color=item.get('color', (37, 99, 235)),
                    label=item['objeto'][:3].upper(),
                )
                filename = f"seed_{det.objeto.split()[0].lower()}.jpg"
                det.imagen.save(filename, image_file, save=False)

            det.save()
            created_count += 1
            self.stdout.write(
                f"Created detection: {det.objeto} ({det.categoria}) [Conf: {det.confianza}]"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {created_count} waste detection records.")
        )
