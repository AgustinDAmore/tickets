# /var/www/tickets/gestion/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (
    show_login_page, 
    login_view, 
    dashboard_view, 
    logout_view,
    crear_usuario_view,
    lista_usuarios_view,
    toggle_usuario_status_view,
    ver_logs_view,
    crear_ticket_view,
    ticket_detalle_view,
    cambiar_contrasena_view,
    crear_aviso_view,
    lista_avisos_view,
    telefonos_view,
    perfil_view,
    gestionar_areas_view,
    cambiar_area_view,
    verificar_acceso_cp,
    gestionar_grupos_view,
    informes_view,
    public_perfil_view,
)

urlpatterns = [
    path('', show_login_page, name='index'),
    path('login/', show_login_page, name='show_login'),
    path('api/login/', login_view, name='process_login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('usuarios/crear/', crear_usuario_view, name='crear_usuario'), 
    path('usuarios/', lista_usuarios_view, name='lista_usuarios'), 
    path('usuarios/toggle/<int:user_id>/', toggle_usuario_status_view, name='toggle_usuario'), 
    path('logs/', ver_logs_view, name='ver_logs'),
    path('tickets/crear/', crear_ticket_view, name='crear_ticket'),
    path('tickets/<int:ticket_id>/', ticket_detalle_view, name='detalle_ticket'),
    path('usuarios/cambiar-contrasena/<int:user_id>/', cambiar_contrasena_view, name='cambiar_contrasena'),
    path('avisos/', lista_avisos_view, name='lista_avisos'),
    path('avisos/crear/', crear_aviso_view, name='crear_aviso'),
    path('telefonos/', telefonos_view, name='telefonos'),
    path('perfil/', perfil_view, name='perfil'),
    path('areas/', gestionar_areas_view, name='gestionar_areas'),
    path('usuarios/cambiar-area/<int:user_id>/', cambiar_area_view, name='cambiar_area'),
    path('usuarios/gestionar-grupos/<int:user_id>/', gestionar_grupos_view, name='gestionar_grupos'),
    path('api/verificar_acceso_cp/', verificar_acceso_cp, name='verificar_acceso_cp_api'),
    path('informes/', informes_view, name='informes'),
    path('usuario/<int:user_id>/', public_perfil_view, name='public_perfil'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'gestion.views.custom_404_view'
handler500 = 'gestion.views.custom_500_view'