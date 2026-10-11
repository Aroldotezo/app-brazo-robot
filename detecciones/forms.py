from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """
    Authentication form styled for Tailwind CSS with Spanish labels, placeholders, and error messages.
    """
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-slate-900 bg-white placeholder-slate-400 shadow-sm',
                'placeholder': 'Ej. lolo o pablito',
                'autocomplete': 'username',
                'id': 'username_input',
                'required': 'required',
            }
        )
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-slate-900 bg-white placeholder-slate-400 shadow-sm',
                'placeholder': '••••••••',
                'autocomplete': 'current-password',
                'id': 'password_input',
                'required': 'required',
            }
        )
    )

    error_messages = {
        'invalid_login': 'Usuario o contraseña incorrectos. Por favor verifique sus credenciales.',
        'inactive': 'Esta cuenta se encuentra inactiva. Contacte al administrador.',
    }
