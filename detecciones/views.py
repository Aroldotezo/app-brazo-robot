from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.viewsets import ModelViewSet

from .models import Deteccion
from .serializers import DeteccionSerializer
from .forms import LoginForm


class DeteccionViewSet(ModelViewSet):
    """
    REST API endpoint to receive and list detection logs from the desktop classification client.
    """
    queryset = Deteccion.objects.all().order_by('-fecha_registro')
    serializer_class = DeteccionSerializer


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