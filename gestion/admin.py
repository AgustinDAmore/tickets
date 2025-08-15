# /var/www/tickets/gestion/admin.py

from django.contrib import admin
from .models import EstadoTicket, Ticket, Comentario

# Registramos los modelos para que aparezcan en el sitio de administración
admin.site.register(EstadoTicket)
admin.site.register(Ticket)
admin.site.register(Comentario)