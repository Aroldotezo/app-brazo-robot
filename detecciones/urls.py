from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeteccionViewSet,
    landing_view,
    login_view,
    logout_view,
    dashboard_view,
)

router = DefaultRouter()
router.register(r'api/detecciones', DeteccionViewSet)

urlpatterns = [
    path('', landing_view, name='landing'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('', include(router.urls)),
]