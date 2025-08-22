# /var/www/tickets/gestion/models.py

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

User = settings.AUTH_USER_MODEL

class Area(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    numero_interno = models.CharField(max_length=20, blank=True, null=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
    try:
        instance.perfil.save()
    except Perfil.DoesNotExist:
        Perfil.objects.create(user=instance)

class EstadoTicket(models.Model):
    nombre_estado = models.CharField(max_length=25, unique=True)
    def __str__(self):
        return self.nombre_estado

class Ticket(models.Model):
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creador = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='tickets_creados')
    estado = models.ForeignKey(EstadoTicket, on_delete=models.RESTRICT)
    area_asignada = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_en_area')
    usuario_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_asignados')

    def __str__(self):
        return self.titulo

class Comentario(models.Model):
    cuerpo_comentario = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comentarios')
    usuario_autor = models.ForeignKey(User, on_delete=models.RESTRICT)

class Aviso(models.Model):
    titulo = models.CharField(max_length=200)
    cuerpo = models.TextField()
    autor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leido_por = models.ManyToManyField(User, related_name='avisos_leidos', blank=True)
    class Meta:
        ordering = ['-fecha_creacion']

class ArchivoAdjunto(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='adjuntos')
    comentario = models.ForeignKey(Comentario, on_delete=models.CASCADE, related_name='adjuntos', null=True, blank=True)
    archivo = models.FileField(upload_to='adjuntos_tickets/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return os.path.basename(self.archivo.name)