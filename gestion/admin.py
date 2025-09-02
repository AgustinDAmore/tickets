# /var/www/tickets/gestion/admin.py

from django.contrib import admin

from .models import (
    Aviso, Area, Perfil, EstadoTicket, Ticket, 
    Comentario, ArchivoAdjunto, Tarea, CategoriaConocimiento, 
    ArticuloConocimiento
)

@admin.register(ArticuloConocimiento)
class ArticuloConocimientoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'autor', 'ultima_actualizacion')
    list_filter = ('categoria', 'autor')
    search_fields = ('titulo', 'contenido')

@admin.register(CategoriaConocimiento)
class CategoriaConocimientoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)

admin.site.register(Area)
admin.site.register(Perfil)
admin.site.register(EstadoTicket)
admin.site.register(Ticket)
admin.site.register(Comentario)
admin.site.register(Aviso)
admin.site.register(ArchivoAdjunto)
admin.site.register(Tarea)