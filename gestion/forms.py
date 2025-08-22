# /var/w ww/tickets/gestion/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.models import User, Group
from .models import Ticket, Comentario, Aviso, Perfil, EstadoTicket, Area

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

class CustomUserCreationForm(UserCreationForm):
    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=False,
        label="Asignar a Área",
        empty_label="Sin área asignada"
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

class TicketCreationForm(forms.ModelForm):
    area_asignada = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        label="Asignar al Área",
        empty_label="Seleccione un área",
        required=True,
        widget=forms.Select(attrs={'class': 'form-field-input'})
    )
    adjuntos = forms.FileField(
        required=False,
        label="Adjuntar archivos (opcional)"
    )

    def __init__(self, *args, **kwargs):
        super(TicketCreationForm, self).__init__(*args, **kwargs)
        self.fields['adjuntos'].widget.attrs.update({
            'multiple': True,
            'class': 'form-field-input'
        })

    class Meta:
        model = Ticket
        fields = ['titulo', 'area_asignada', 'descripcion', 'adjuntos']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-field-input'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-field-input', 'rows': 5}),
        }
        labels = {
            'titulo': 'Título del Ticket',
            'descripcion': 'Descripción del Problema',
        }

class CommentForm(forms.ModelForm):
    adjuntos = forms.FileField(
        required=False,
        label="Adjuntar archivos",
    )
    
    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['adjuntos'].widget.attrs.update({
            'multiple': True,
            'class': 'form-field-input mt-2'
        })

    class Meta:
        model = Comentario
        fields = ['cuerpo_comentario', 'adjuntos']
        widgets = {
            'cuerpo_comentario': forms.Textarea(attrs={
                'class': 'form-field-input', 'rows': 3, 'placeholder': 'Escribe tu comentario aquí...'
            }),
        }
        labels = {'cuerpo_comentario': ''}


class StatusChangeForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['estado']
        widgets = {'estado': forms.Select(attrs={'class': 'form-field-input'})}
        labels = {'estado': 'Cambiar Estado del Ticket'}

class AdminPasswordChangeForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
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

class UserGroupsForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Grupos"
    )

    class Meta:
        model = User
        fields = ['groups']