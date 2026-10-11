from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.viewsets import ModelViewSet
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Deteccion
from .serializers import DeteccionSerializer
from .forms import LoginForm


class DeteccionViewSet(ModelViewSet):
    """
    REST API endpoint to receive and list detection logs from the desktop classification client.
    Broadcasts newly created detection records to connected WebSocket clients in real time.
    """
    queryset = Deteccion.objects.all().order_by('-fecha_registro')
    serializer_class = DeteccionSerializer

    def perform_create(self, serializer):
        instance = serializer.save()

        # Broadcast new detection event to WebSocket subscribers
        channel_layer = get_channel_layer()
        if channel_layer:
            event_payload = {
                'id': instance.id,
                'objeto': instance.objeto,
                'categoria': instance.categoria,
                'confianza': float(instance.confianza),
                'camara_id': instance.camara_id,
                'imagen_url': instance.imagen.url if instance.imagen else None,
                'fecha_registro': instance.fecha_registro.strftime('%d/%m/%Y %H:%M:%S'),
            }
            async_to_sync(channel_layer.group_send)(
                f"camera_{instance.camara_id}",
                {
                    'type': 'detection_event',
                    'data': event_payload,
                }
            )
            async_to_sync(channel_layer.group_send)(
                "camera_all",
                {
                    'type': 'detection_event',
                    'data': event_payload,
                }
            )



def landing_view(request):
    """
    Public landing page presenting the waste classification project,
    its core features, architecture, and system benefits.
    """
    total_detections = Deteccion.objects.count()
    organic_count = Deteccion.objects.filter(categoria__iexact='organico').count()
    inorganic_count = Deteccion.objects.filter(categoria__iexact='inorganico').count()

    context = {
        'total_detections': total_detections,
        'organic_count': organic_count,
        'inorganic_count': inorganic_count,
    }
    return render(request, 'detecciones/landing.html', context)


def login_view(request):
    """
    Handles user authentication. Validates credentials, sets session,
    and redirects authenticated users to the monitoring dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"¡Bienvenido al sistema, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
            return redirect(next_url)
    else:
        form = LoginForm(request)

    return render(request, 'detecciones/login.html', {'form': form})


def logout_view(request):
    """
    Logs out the current user and redirects back to the public landing page.
    """
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('landing')


@login_required(login_url='login')
def dashboard_view(request):
    """
    Protected dashboard showing real-time waste detections, key metrics,
    and recent image captures. Restricted to authenticated users.
    """
    detections = Deteccion.objects.all().order_by('-fecha_registro')[:50]
    total_detections = Deteccion.objects.count()
    organic_count = Deteccion.objects.filter(categoria__iexact='organico').count()
    inorganic_count = Deteccion.objects.filter(categoria__iexact='inorganico').count()

    context = {
        'detecciones': detections,
        'total': total_detections,
        'organic_count': organic_count,
        'inorganic_count': inorganic_count,
    }
    return render(request, 'detecciones/dashboard.html', context)