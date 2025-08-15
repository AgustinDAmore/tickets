# /var/www/tickets/gestion/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Ticket, Comentario, Aviso, Perfil, EstadoTicket, Area

# --- Formulario para crear Áreas ---
class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-field-input'}),
        }
        labels = {
            'nombre': 'Nombre del Área',
        }

# --- Formulario de Creación de Usuario (actualizado con Áreas) ---
class CustomUserCreationForm(UserCreationForm):
    es_administrador = forms.BooleanField(label="¿Es administrador?", required=False)
    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=False,
        label="Asignar a Área",
        empty_label="Sin área asignada"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('es_administrador', 'area')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data.get("es_administrador", False)
        if commit:
            user.save()
            # Guardamos el área en el perfil del usuario
            user.perfil.area = self.cleaned_data.get('area')
            user.perfil.save()
        return user

# --- Formulario de Creación de Ticket (actualizado con Áreas) ---
class TicketCreationForm(forms.ModelForm):
    area_asignada = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        label="Asignar al Área",
        empty_label="Seleccione un área",
        required=True,
        widget=forms.Select(attrs={'class': 'form-field-input'})
    )
    class Meta:
        model = Ticket
        fields = ['titulo', 'area_asignada', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-field-input'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-field-input', 'rows': 5}),
        }
        labels = {
            'titulo': 'Título del Ticket',
            'descripcion': 'Descripción del Problema',
        }

# --- Formulario para Añadir Comentarios ---
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['cuerpo_comentario']
        widgets = {
            'cuerpo_comentario': forms.Textarea(attrs={
                'class': 'form-field-input', 'rows': 3, 'placeholder': 'Escribe tu comentario aquí...'
            }),
        }
        labels = {'cuerpo_comentario': ''}

# --- Formulario para Cambiar Estado de Ticket ---
class StatusChangeForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['estado']
        widgets = {'estado': forms.Select(attrs={'class': 'form-field-input'})}
        labels = {'estado': 'Cambiar Estado del Ticket'}

# --- Formularios de Gestión de Usuarios ---
class AdminPasswordChangeForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        # Aquí solo incluimos el campo que queremos que se pueda modificar.
        fields = ['numero_interno']
        labels = {
            'numero_interno': 'Nuevo Número de Interno/Teléfono'
        }
        widgets = {
            'numero_interno': forms.TextInput(attrs={'class': 'form-field-input'}),
        }

class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-field-input'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-field-input'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-field-input'})

# --- Formulario para Crear Avisos ---
class AvisoForm(forms.ModelForm):
    class Meta:
        model = Aviso
        fields = ['titulo', 'cuerpo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-field-input'}),
            'cuerpo': forms.Textarea(attrs={'class': 'form-field-input', 'rows': 6}),
        }
        labels = {'titulo': 'Título del Aviso', 'cuerpo': 'Mensaje'}

class AreaChangeForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['area']
        labels = {'area': ''}
        widgets = {'area': forms.Select(attrs={'class': 'form-field-input'})}