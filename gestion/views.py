# /var/www/tickets/gestion/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import logging
import os
import json
import csv
import logging

from django.http import HttpResponse
from webpush import send_user_notification

from .models import Ticket, EstadoTicket, Aviso, Perfil, Area, ArchivoAdjunto
from .forms import (
    CustomUserCreationForm, TicketCreationForm, CommentForm,
    StatusChangeForm, AdminPasswordChangeForm, AvisoForm,
    PerfilUpdateForm, UserPasswordChangeForm, AreaForm,
    AreaChangeForm, UserGroupsForm
)

audit_log = logging.getLogger('audit')
User = get_user_model()

# --- VISTAS DE LOGIN Y LOGOUT ---

def show_login_page(request: HttpRequest) -> HttpResponse:
    return render(request, 'gestion/login.html')

@require_POST
def login_view(request: HttpRequest) -> HttpResponse:
    try:
        data = json.loads(request.body)
        username = data.get('nombre_usuario')
        password = data.get('password')
        username = username.lower()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            audit_log.info(f"INICIO DE SESIÓN: Usuario '{user.username}' ha iniciado sesión.")
            return JsonResponse({'success': True, 'redirect_url': '/dashboard/'})
        else:
            audit_log.warning(f"INTENTO DE LOGIN FALLIDO: Para el usuario '{username}'.")
            return HttpResponse('Credenciales inválidas.', status=401)
    except Exception as e:
        audit_log.error(f"ERROR EN LOGIN: {e}")
        return HttpResponse('Ha ocurrido un error en el servidor.', status=500)

def logout_view(request: HttpRequest) -> HttpResponse:
    user = request.user
    audit_log.info(f"CIERRE DE SESIÓN: Usuario '{user.username}' ha cerrado sesión.")
    logout(request)
    return redirect('show_login')

# --- VISTA DEL DASHBOARD (CORREGIDA) ---

@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    view_mode = request.GET.get('vista', 'personal')
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('estado', '')
    creator_filter = request.GET.get('creador', '')

    tickets = Ticket.objects.select_related('estado', 'usuario_creador', 'area_asignada')

    user_can_view_all_tickets = request.user.groups.filter(name='Ver todos los tickets').exists()

    if user_can_view_all_tickets and view_mode == 'todos':
        current_view_name = "Todos los Tickets"
        tickets = tickets.all()
    else:
        current_view_name = "Mis Tickets"
        user_area = request.user.perfil.area
        
        if user_area:
            tickets = tickets.filter(
                Q(usuario_creador=request.user) | Q(area_asignada=user_area)
            ).distinct()
        else:
            tickets = tickets.filter(usuario_creador=request.user)

    if search_query:
        tickets = tickets.filter(
            Q(titulo__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(descripcion__icontains=search_query)
        )
    
    if status_filter:
        tickets = tickets.filter(estado__id=status_filter)

    if creator_filter and user_can_view_all_tickets and view_mode == 'todos':
        tickets = tickets.filter(usuario_creador__id=creator_filter)

    tickets = tickets.order_by('-fecha_creacion')
    
    user_can_see_informe = request.user.groups.filter(name='Informe').exists()

    context = {
        'user': request.user,
        'tickets': tickets,
        'all_statuses': EstadoTicket.objects.all(),
        'search_query': search_query,
        'status_filter': status_filter,
        'creator_filter': creator_filter,
        'unread_avisos_count': Aviso.objects.exclude(leido_por=request.user).count(),
        'current_view_name': current_view_name,
        'view_mode': view_mode,
        'user_can_view_all_tickets': user_can_view_all_tickets,
        'user_can_see_informe': user_can_see_informe,
    }
    
    if user_can_view_all_tickets:
        context['all_users'] = User.objects.filter(is_active=True).order_by('username')
    
    return render(request, 'gestion/dashboard.html', context)

# --- VISTAS DE GESTIÓN DE ÁREAS (SOLO ADMINS) ---

@login_required
def gestionar_areas_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            area_nueva = form.save()
            audit_log.info(f"ÁREA CREADA: Admin '{request.user.username}' creó el área '{area_nueva.nombre}'.")
            messages.success(request, 'Área creada exitosamente.')
            return redirect('gestionar_areas')
    else:
        form = AreaForm()
        
    context = {
        'form': form,
        'areas': Area.objects.all().order_by('nombre')
    }
    return render(request, 'gestion/gestionar_areas.html', context)

# --- VISTAS DE GESTIÓN DE TICKETS ---

@login_required
def crear_ticket_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = TicketCreationForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.usuario_creador = request.user
            try:
                ticket.estado = EstadoTicket.objects.get(nombre_estado='Pendiente')
            except EstadoTicket.DoesNotExist:
                return HttpResponse("Error: El estado 'Pendiente' no está configurado.", status=500)
            
            ticket.save()

            for f in request.FILES.getlist('adjuntos'):
                ArchivoAdjunto.objects.create(ticket=ticket, archivo=f, comentario=None)

            audit_log.info(f"TICKET CREADO: Usuario '{request.user.username}' creó el ticket #{ticket.id} '{ticket.titulo}'.")

            print(">>> INICIANDO PROCESO DE NOTIFICACIÓN <<<")
            area_asignada = ticket.area_asignada
            if area_asignada:
                print(f"Ticket asignado al área: {area_asignada.nombre}")
                
                usuarios_a_notificar = User.objects.filter(perfil__area=area_asignada, is_active=True)
                print(f"Usuarios encontrados en esta área: {usuarios_a_notificar.count()}")

                if not usuarios_a_notificar.exists():
                    print("No se encontraron usuarios para notificar en esta área.")

                payload = {
                    "head": "Nuevo Ticket Asignado a tu Área",
                    "body": f"Asunto: '{ticket.titulo}'",
                    "url": f"/tickets/{ticket.id}/"
                }

                for usuario in usuarios_a_notificar:
                    print(f"Intentando notificar a: {usuario.username}")
                    if usuario == request.user:
                        print(f"...saltando notificación para el creador del ticket ({usuario.username}).")
                        continue
                    try:
                        send_user_notification(user=usuario, payload=payload, ttl=1000)
                        print(f"¡Notificación enviada exitosamente a {usuario.username}!")
                    except Exception as e:
                        print(f"!!! ERROR enviando notificación a {usuario.username}: {e}")
            else:
                print("El ticket no tiene un área asignada, no se enviarán notificaciones.")
            
            print(">>> FIN DEL PROCESO DE NOTIFICACIÓN <<<")

            return redirect('dashboard')
    else:
        form = TicketCreationForm()
    
    return render(request, 'gestion/crear_ticket.html', {'form': form})

@login_required
def ticket_detalle_view(request: HttpRequest, ticket_id: int) -> HttpResponse:
    try:
        ticket = Ticket.objects.select_related('estado', 'usuario_creador', 'area_asignada', 'usuario_asignado').get(id=ticket_id)
    except Ticket.DoesNotExist:
        return redirect('dashboard')

    # --- INICIO DE LA VALIDACIÓN DE PERMISOS ---
    user = request.user
    
    # Condición 1: ¿Es admin o tiene permiso para ver todos los tickets?
    can_view_all = user.is_staff or user.groups.filter(name='Ver todos los tickets').exists()
    
    # Condición 2: ¿Es el creador del ticket?
    is_creator = ticket.usuario_creador == user
    
    # Condición 3: ¿Está asignado al ticket?
    is_assigned = ticket.usuario_asignado == user
    
    # Condición 4: ¿Pertenece al área del ticket?
    is_in_area = False
    try:
        # Verificamos que el usuario tenga un perfil y un área asignada.
        if hasattr(user, 'perfil') and user.perfil.area:
            if user.perfil.area == ticket.area_asignada:
                is_in_area = True
    except Perfil.DoesNotExist:
        # Si el usuario no tiene perfil, no puede pertenecer a un área.
        pass

    # Si NINGUNA de las condiciones se cumple, el acceso es denegado.
    if not (can_view_all or is_creator or is_assigned or is_in_area):
        messages.error(request, "No tienes permiso para ver este ticket.")
        return redirect('dashboard')
    # --- FIN DE LA VALIDACIÓN DE PERMISOS ---

    comment_form = CommentForm()
    status_form = StatusChangeForm(instance=ticket)

    if request.method == 'POST':
        if 'add_comment' in request.POST:
            comment_form = CommentForm(request.POST, request.FILES)
            if comment_form.is_valid():
                # Auto-asignación si el usuario es del área y el ticket no tiene a nadie asignado
                if not ticket.usuario_asignado and is_in_area:
                    ticket.usuario_asignado = user
                    ticket.save()
                    audit_log.info(f"TICKET ASIGNADO: Usuario '{user.username}' se auto-asignó el ticket #{ticket.id}.")

                new_comment = comment_form.save(commit=False)
                new_comment.ticket = ticket
                new_comment.usuario_autor = user
                new_comment.save()

                for f in request.FILES.getlist('adjuntos'):
                    ArchivoAdjunto.objects.create(ticket=ticket, comentario=new_comment, archivo=f)

                audit_log.info(f"COMENTARIO AÑADIDO: Usuario '{user.username}' comentó en el ticket #{ticket.id}.")
                return redirect('detalle_ticket', ticket_id=ticket.id)

        elif 'update_status' in request.POST:
            old_status = ticket.estado.nombre_estado
            status_form = StatusChangeForm(request.POST, instance=ticket)
            if status_form.is_valid():
                updated_ticket = status_form.save()
                new_status = updated_ticket.estado.nombre_estado
                audit_log.info(f"CAMBIO DE ESTADO: Usuario '{user.username}' cambió el estado del ticket #{ticket.id} de '{old_status}' a '{new_status}'.")
                return redirect('detalle_ticket', ticket_id=ticket.id)
    
    context = {'ticket': ticket, 'comment_form': comment_form, 'status_form': status_form, 'user': user}
    return render(request, 'gestion/ticket_detalle.html', context)
    
# --- VISTAS DE GESTIÓN DE USUARIOS Y PERFIL ---

@login_required
def lista_usuarios_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return redirect('dashboard')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user_to_change = User.objects.get(id=user_id)

        if user_to_change != request.user:
            if action == 'change_area':
                area_id = request.POST.get('area_id')
                if area_id:
                    new_area = Area.objects.get(id=area_id)
                    user_to_change.perfil.area = new_area
                else:
                    user_to_change.perfil.area = None
                user_to_change.perfil.save()
                messages.success(request, f"Área de {user_to_change.username} actualizada.")
        
        return redirect('lista_usuarios')

    # Lógica de búsqueda para peticiones GET
    search_query = request.GET.get('q', '')
    
    usuarios = User.objects.select_related('perfil', 'perfil__area').prefetch_related('groups').all().order_by('username')

    if search_query:
        usuarios = usuarios.filter(username__icontains=search_query)

    all_areas = Area.objects.all().order_by('nombre')
    context = {
        'usuarios': usuarios,
        'all_areas': all_areas,
        'search_query': search_query,
    }
    return render(request, 'gestion/lista_usuarios.html', context)

@login_required
def crear_usuario_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            audit_log.info(f"USUARIO CREADO: Admin '{request.user.username}' creó al usuario '{new_user.username}'.")
            messages.success(request, '¡Usuario creado exitosamente!')
            return redirect('lista_usuarios')
    else:
        form = CustomUserCreationForm()
    return render(request, 'gestion/crear_usuario.html', {'form': form})

@login_required
@require_POST
def toggle_usuario_status_view(request: HttpRequest, user_id: int) -> HttpResponse:
    if not request.user.is_staff:
        return redirect('dashboard')
    try:
        usuario_a_modificar = User.objects.get(id=user_id)
        if usuario_a_modificar.id != request.user.id:
            new_status = "Habilitado" if not usuario_a_modificar.is_active else "Deshabilitado"
            usuario_a_modificar.is_active = not usuario_a_modificar.is_active
            usuario_a_modificar.save()
            audit_log.info(f"ESTADO DE USUARIO: Admin '{request.user.username}' ha cambiado el estado de '{usuario_a_modificar.username}' a '{new_status}'.")
    except User.DoesNotExist:
        pass
    return redirect('lista_usuarios')

@login_required
def cambiar_contrasena_view(request: HttpRequest, user_id: int) -> HttpResponse:
    if not request.user.is_staff:
        return redirect('dashboard')
    try:
        user_to_change = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('lista_usuarios')
    if request.method == 'POST':
        form = AdminPasswordChangeForm(user_to_change, request.POST)
        if form.is_valid():
            form.save()
            audit_log.info(f"CAMBIO DE CONTRASEÑA: Admin '{request.user.username}' cambió la contraseña para el usuario '{user_to_change.username}'.")
            messages.success(request, f'¡Contraseña para {user_to_change.username} cambiada exitosamente!')
            return redirect('lista_usuarios')
    else:
        form = AdminPasswordChangeForm(user_to_change)
    context = {'form': form, 'user_to_change': user_to_change}
    return render(request, 'gestion/cambiar_contrasena.html', context)

@login_required
def perfil_view(request: HttpRequest) -> HttpResponse:
    perfil, created = Perfil.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = PerfilUpdateForm(request.POST, instance=perfil)
            password_form = UserPasswordChangeForm(request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, '¡Tu perfil ha sido actualizado exitosamente!')
                return redirect('perfil')
        elif 'change_password' in request.POST:
            password_form = UserPasswordChangeForm(request.user, request.POST)
            profile_form = PerfilUpdateForm(request.POST, instance=perfil)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, '¡Tu contraseña ha sido cambiada exitosamente!')
                return redirect('perfil')
            else:
                profile_form = PerfilUpdateForm(instance=perfil)
    else:
        profile_form = PerfilUpdateForm(instance=perfil)
        password_form = UserPasswordChangeForm(request.user)
    context = {'profile_form': profile_form, 'password_form': password_form}
    return render(request, 'gestion/perfil.html', context)

# --- VISTAS DE AVISOS ---

@login_required
def crear_aviso_view(request: HttpRequest) -> HttpResponse:
    if not request.user.groups.filter(name='Enviar Avisos').exists():
        return redirect('dashboard')
    if request.method == 'POST':
        form = AvisoForm(request.POST)
        if form.is_valid():
            aviso = form.save(commit=False)
            aviso.autor = request.user
            aviso.save()
            audit_log.info(f"AVISO CREADO: Admin '{request.user.username}' creó el aviso '{aviso.titulo}'.")
            return redirect('lista_avisos')
    else:
        form = AvisoForm()
    return render(request, 'gestion/crear_aviso.html', {'form': form})

@login_required
def lista_avisos_view(request: HttpRequest) -> HttpResponse:
    avisos = Aviso.objects.all()
    user_can_send_avisos = request.user.groups.filter(name='Enviar Avisos').exists()
    for aviso in avisos:
        aviso.leido_por.add(request.user)
    context = {
        'avisos': avisos,
        'user_can_send_avisos': user_can_send_avisos,
    }
    return render(request, 'gestion/lista_avisos.html', context)

# --- VISTA DE LOGS (SOLO ADMINS) ---

@login_required
def ver_logs_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return redirect('dashboard')
    log_file_path = os.path.join(settings.BASE_DIR, 'audit.log')
    log_lines = []
    try:
        with open(log_file_path, 'r') as f:
            log_lines = f.readlines()[::-1]
    except FileNotFoundError:
        log_lines = ["El archivo de auditoría no ha sido creado todavía."]
    return render(request, 'gestion/ver_logs.html', {'log_lines': log_lines})

# --- VISTA DE DIRECTORIO TELEFÓNICO ---
@login_required
def telefonos_view(request: HttpRequest) -> HttpResponse:
    directorio = []
    csv_file_path = os.path.join(settings.BASE_DIR, 'directorio.csv')
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:
                    nombre = row[0].replace('"', '').strip()
                    interno = row[1].strip()
                    if nombre and interno: 
                        directorio.append({'nombre': nombre, 'interno': interno})
    except FileNotFoundError:
        print(f"ADVERTENCIA: El archivo 'directorio.csv' no se encontró en {csv_file_path}")
    context = {'directorio': directorio}
    return render(request, 'gestion/telefonos.html', context)

@login_required
def cambiar_area_view(request: HttpRequest, user_id: int) -> HttpResponse:
    if not request.user.is_staff:
        return redirect('dashboard')
    try:
        user_to_change = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('lista_usuarios')

    if request.method == 'POST':
        form = AreaChangeForm(request.POST, instance=user_to_change.perfil)
        if form.is_valid():
            form.save()
            messages.success(request, f'Área para {user_to_change.username} cambiada exitosamente.')
            return redirect('lista_usuarios')
    else:
        form = AreaChangeForm(instance=user_to_change.perfil)

    context = {'form': form, 'user_to_change': user_to_change}
    return render(request, 'gestion/cambiar_area.html', context)

@login_required
def gestionar_grupos_view(request: HttpRequest, user_id: int) -> HttpResponse:
    if not request.user.is_staff:
        return redirect('dashboard')
    try:
        user_to_manage = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('lista_usuarios')

    if request.method == 'POST':
        form = UserGroupsForm(request.POST, instance=user_to_manage)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grupos para {user_to_manage.username} actualizados exitosamente!')
            return redirect('lista_usuarios')
    else:
        form = UserGroupsForm(instance=user_to_manage)

    context = {'form': form, 'user_to_manage': user_to_manage}
    return render(request, 'gestion/gestionar_grupos.html', context)

@login_required
def informes_view(request: HttpRequest) -> HttpResponse:
    if not request.user.groups.filter(name='Informe').exists():
        return redirect('dashboard')

    total_tickets = Ticket.objects.count()
    tickets_pendientes = Ticket.objects.filter(estado__nombre_estado='Pendiente').count()
    tickets_aceptados = Ticket.objects.filter(estado__nombre_estado='Aceptado').count()
    tickets_finalizados = Ticket.objects.filter(estado__nombre_estado='Finalizado').count()
    usuarios_activos = User.objects.filter(is_active=True).count()

    porcentaje_tickets_pendientes = (tickets_pendientes/total_tickets)*100
    porcentaje_tickets_aceptados = (tickets_aceptados/total_tickets)*100
    porcentaje_tickets_finalizados = (tickets_finalizados/total_tickets)*100
    porcentaje_tickets_sin_finalizar = porcentaje_tickets_aceptados + porcentaje_tickets_pendientes

    context = {
        'total_tickets': total_tickets,
        'porcentaje_tickets_pendientes': porcentaje_tickets_pendientes,
        'tickets_pendientes': tickets_pendientes,
        'porcentaje_tickets_aceptados': porcentaje_tickets_aceptados,
        'tickets_aceptados': tickets_aceptados,
        'porcentaje_tickets_finalizados': porcentaje_tickets_finalizados,
        'porcentaje_tickets_sin_finalizar': porcentaje_tickets_sin_finalizar,
        'tickets_sin_finalizar': tickets_aceptados+tickets_pendientes,
        'tickets_finalizados': tickets_finalizados,
        'usuarios_activos': usuarios_activos,
    }
    return render(request, 'gestion/informes.html', context)


def custom_404_view(request):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)

###########################################################################
# Servicios
###########################################################################
logger = logging.getLogger(__name__)
User = get_user_model()

@csrf_exempt
def verificar_acceso_cp(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

    try:
        # Leemos el cuerpo de la petición
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'status': 'error', 'message': 'Faltan credenciales.'}, status=400)

        # --- BÚSQUEDA DE USUARIO A PRUEBA DE ERRORES ---
        # Buscamos el usuario por su username, sin distinguir mayúsculas/minúsculas
        user = User.objects.filter(username__iexact=username).first()

        # Verificamos si el usuario existe Y si la contraseña es correcta
        if user and user.check_password(password):
            if user.is_active:
                # Si las credenciales son correctas, verificamos el permiso
                if user.groups.filter(name='CP Access').exists():
                    return JsonResponse({'status': 'ok', 'message': 'Acceso concedido.'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Usuario no tiene permisos para CP.'}, status=403)
            else:
                return JsonResponse({'status': 'error', 'message': 'La cuenta de usuario está inactiva.'}, status=403)
        else:
            # Si el usuario no existe o la contraseña no coincide
            return JsonResponse({'status': 'error', 'message': 'Credenciales inválidas.'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Error en el formato de datos (JSON).'}, status=400)
    except Exception as e:
        # Capturamos cualquier otro error inesperado para poder verlo
        # Revisa los logs de 'tickets' si el error persiste
        print(f"ERROR INESPERADO en verificar_acceso_cp: {e}")
        return JsonResponse({'status': 'error', 'message': 'Error interno del servidor.'}, status=500)