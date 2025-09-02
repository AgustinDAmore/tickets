# /var/www/tickets/gestion/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.models import User, Group
from .models import Ticket, Comentario, Aviso, Perfil, EstadoTicket, Area, Tarea

class MultipleFileInputMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'adjuntos' in self.fields:
            self.fields['adjuntos'].widget.attrs.update({
                'multiple': True,
                'class': 'form-field-input'
            })

class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-field-input')

class AreaForm(BaseForm):
    class Meta:
        model = Area
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre del Área',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if Area.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe un área con este nombre.")
        return nombre

class UserUpdateForm(BaseForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
        }
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'ejemplo@dominio.com'}),
        }


class CustomUserCreationForm(UserCreationForm):
    area = forms.ModelChoiceField(
        queryset=Area.objects.all().order_by('nombre'),
        required=True,
        label="Asignar a Área",
        empty_label="Seleccione un área"
    )
    
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Grupos"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('area', 'groups',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.username.lower()
        if commit:
            user.save()
            user.perfil.area = self.cleaned_data.get('area')
            user.perfil.save()
            user.groups.set(self.cleaned_data.get('groups'))
        return user

class TicketCreationForm(MultipleFileInputMixin, BaseForm):
    area_asignada = forms.ModelChoiceField(
        queryset=Area.objects.order_by('nombre'),
        label="Asignar al Área",
        empty_label="Seleccione un área",
        required=True
    )
    adjuntos = forms.FileField(
        required=False,
        label="Adjuntar archivos (opcional)"
    )

    class Meta:
        model = Ticket
        fields = ['titulo', 'area_asignada', 'descripcion', 'adjuntos']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'titulo': 'Título del Ticket',
            'descripcion': 'Descripción del Problema',
        }

class TareaCreationForm(BaseForm):
    areas_asignadas = forms.ModelMultipleChoiceField(
        queryset=Area.objects.order_by('nombre'),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Seleccionar Áreas"
    )

    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'areas_asignadas']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'titulo': 'Título de la Tarea',
            'descripcion': 'Descripción General',
        }

class CommentForm(MultipleFileInputMixin, BaseForm):
    adjuntos = forms.FileField(
        required=False,
        label="Adjuntar archivos",
    )

    class Meta:
        model = Comentario
        fields = ['cuerpo_comentario', 'adjuntos']
        widgets = {
            'cuerpo_comentario': forms.Textarea(attrs={
                'rows': 3, 'placeholder': 'Escribe tu comentario aquí...'
            }),
        }
        labels = {'cuerpo_comentario': ''}

class StatusChangeForm(BaseForm):
    class Meta:
        model = Ticket
        fields = ['estado']
        labels = {'estado': 'Cambiar Estado del Ticket'}

class AdminPasswordChangeForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': 'form-field-input'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-field-input'})

class PerfilUpdateForm(BaseForm):
    class Meta:
        model = Perfil
        fields = ['numero_interno']
        labels = {
            'numero_interno': 'Nuevo Número de Interno/Teléfono'
        }

class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-field-input'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-field-input'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-field-input'})

class AvisoForm(BaseForm):
    class Meta:
        model = Aviso
        fields = ['titulo', 'cuerpo']
        widgets = {
            'cuerpo': forms.Textarea(attrs={'rows': 6}),
        }
        labels = {'titulo': 'Título del Aviso', 'cuerpo': 'Mensaje'}

class AreaChangeForm(BaseForm):
    class Meta:
        model = Perfil
        fields = ['area']
        labels = {'area': ''}

class UserGroupsForm(BaseForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Grupos"
    )

    class Meta:
        model = User
        fields = ['groups']