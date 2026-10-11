from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Deteccion


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for the custom User model.
    """
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('phone', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('phone', 'role')}),
    )
    list_display = ('username', 'email', 'first_name', 'phone', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'email', 'phone')


@admin.register(Deteccion)
class DeteccionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Deteccion model.
    """
    list_display = ('id', 'objeto', 'categoria', 'confianza', 'camara_id', 'fecha_registro')
    list_filter = ('categoria', 'camara_id', 'fecha_registro')
    search_fields = ('objeto', 'camara_id')
