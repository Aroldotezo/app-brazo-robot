from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model extending AbstractUser with phone number and system role.
    """
    ROLE_ADMIN = 'admin'
    ROLE_OPERATOR = 'operator'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrador'),
        (ROLE_OPERATOR, 'Operador'),
    ]

    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_OPERATOR,
        verbose_name="Rol"
    )

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_operator(self):
        return self.role == self.ROLE_OPERATOR

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Deteccion(models.Model):
    """
    Model representing waste detection events captured by the camera system.
    """
    objeto = models.CharField(max_length=100)        # Detected object name: e.g. "Botella de plástico", "Manzana"
    categoria = models.CharField(max_length=50)       # Classification: "Orgánico" or "Inorgánico"
    confianza = models.FloatField()                  # Confidence score: e.g. 0.95
    camara_id = models.CharField(max_length=50, default="CAM_01")  # Camera identifier or location
    imagen = models.ImageField(upload_to='capturas/', blank=True, null=True)  # Snapshot image
    fecha_registro = models.DateTimeField(auto_now_add=True)  # Timestamp generated on creation

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = "Detección"
        verbose_name_plural = "Detecciones"

    def __str__(self):
        return f"{self.objeto} ({self.categoria}) - {self.fecha_registro.strftime('%Y-%m-%d %H:%M')}"