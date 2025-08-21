# /var/www/tickets/gestion/admin.py

from django.contrib import admin
from .models import Aviso, Area, Perfil, EstadoTicket, Ticket, Comentario, ArchivoAdjunto

# Registramos los modelos para que aparezcan en el sitio de administración
admin.site.register(Area)
admin.site.register(Perfil)
admin.site.register(EstadoTicket)
admin.site.register(Ticket)
admin.site.register(Comentario)
admin.site.register(Aviso)
admin.site.register(ArchivoAdjunto)