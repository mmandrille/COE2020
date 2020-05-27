#imports de Python
import csv
import math
from datetime import time, datetime, timedelta
#Imports de Django
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib.auth.decorators import permission_required
#Imports del proyecto
from coe.settings import SEND_MAIL
from core.forms import SearchForm, UploadFoto, FileForm
from core.forms import EmailForm
from core.functions import delete_tags
from georef.models import Ubicacion
from informacion.models import Individuo, Atributo, Relacion, Documento, Domicilio
from informacion.functions import actualizar_individuo
from operadores.functions import obtener_operador
#Impors de la app
from .tokens import account_activation_token, token_provision
from .choices import TIPO_DISPOSITIVO
from .models import Inscripcion, Area, Tarea, TareaElegida, Dispositivo
from .models import Turno
from .models import Capacitacion
from .models import ProyectoEstudiantil
from .models import EmailsInscripto
from .models import Organization, DomicilioOrganizacion, Peticionp, Emails_Peticionp
from .forms import ProfesionalSaludForm, VoluntarioSocialForm
from .forms import ProyectoEstudiantilForm, IndividuoForm
from .forms import OrganizationForm, EmpleadoForm
from .forms import PeticionpForm
from .forms import PersonapForm, AprobarForm, ResponsableForm
from .models import Emails_Peticiones_Organization, Responsable
from .models import Empleado

# Create your views here.
def inscripcion_salud(request):
    form = ProfesionalSaludForm()
    if request.method == "POST":
        try:#Tratamos de obtener el dni
            num_doc = request.POST['num_doc']
            individuo = Individuo.objects.get(num_doc=num_doc)
        except Individuo.DoesNotExist:
            individuo = None
        form = ProfesionalSaludForm(request.POST, request.FILES, instance=individuo)
        if form.is_valid():
            individuo = actualizar_individuo(form)
            #Armamos la inscripcion:
            inscripto = Inscripcion()
            inscripto.tipo_inscripto = 'PS'
            inscripto.individuo = individuo
            inscripto.profesion = form.cleaned_data['profesion']
            inscripto.matricula = form.cleaned_data['matricula']
            inscripto.info_extra = form.cleaned_data['info_extra']
            #Agregamos documentos
            #Creamos doc:
            documento = Documento(individuo=individuo)
            documento.tipo = 'DI'
            documento.archivo = form.cleaned_data['frente_dni']
            documento.aclaracion = 'FRENTE'
            documento.save()
            #Cargamos titulo:
            documento = Documento(individuo=individuo)
            documento.tipo = 'TP'
            documento.archivo = form.cleaned_data['archivo_titulo']
            documento.aclaracion = 'Titulo Profesional'
            documento.save()
            #guardamos
            inscripto.save()
            #enviar email de validacion
            if SEND_MAIL:
                to_email = individuo.email
                #Preparamos el correo electronico
                mail_subject = 'Inscripcion al COE2020'
                message = render_to_string('emails/acc_active_inscripcion_salud.html', {
                        'inscripto': inscripto,
                    })
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                #Enviamos el correo
                email.send()
            return render(request, 'inscripto_exito.html', {'inscripto': inscripto, })
    return render(request, "inscripcion_salud.html", {
        'titulo': "Inscribite",
        'form': form, 
        'boton': "Inscribirse",
    })

def inscripcion_social(request):
    dispositivos = TIPO_DISPOSITIVO
    areas = Area.objects.all()
    form = VoluntarioSocialForm()
    if request.method == "POST":
        try:#Tratamos de obtener el dni y el individuo
            num_doc = request.POST['num_doc']
            individuo = Individuo.objects.get(num_doc=num_doc)
            if individuo.situacion_actual:
                if individuo.situacion_actual.conducta in ('D', 'E'):
                    return render(request, 'extras/error.html', {
                        'titulo': 'Inscripcion Denegada',
                        'error': "Usted se encuentra bajo Aislamiento, Contacte al Administrador.",
                    })
        except Individuo.DoesNotExist:
            individuo = None
        form = VoluntarioSocialForm(request.POST, request.FILES, instance=individuo)
        if form.is_valid():
            #Obtenemos CheckBoxes
            #tareas = request.POST.getlist('tareas')
            dispositivos = request.POST.getlist('dispositivos')
            #Actualizamos Individuo
            individuo = actualizar_individuo(form)
            #Evitamos Repetidos
            individuo.voluntariados.filter(valido=False).delete()
            if individuo.voluntariados.exists():
                return render(request, 'extras/error.html', {
                    'titulo': 'Inscripcion Previa Validada',
                    'error': "Usted ya cuenta con una inscripcion valida realizada.",
                })
            #Creamos diccionario de tareas
            #dict_tareas = {t.id:t for t in Tarea.objects.all()}
            #Armamos la inscripcion:
            inscripto = Inscripcion()
            inscripto.tipo_inscripto = 'VS'
            inscripto.individuo = individuo
            inscripto.oficio = form.cleaned_data['oficio']
            inscripto.info_extra = form.cleaned_data['info_extra']
            #Guardamos
            inscripto.save()
            #Dispositivos
            for disp in dispositivos:
                dispositivo = Dispositivo(inscripto=inscripto)
                dispositivo.tipo = disp
                dispositivo.save()
            #enviar email de validacion
            if SEND_MAIL:
                to_email = individuo.email
                #Preparamos el correo electronico
                mail_subject = 'Inscripcion al COE2020'
                message = render_to_string('emails/acc_active_inscripcion_social.html', {
                        'inscripto': inscripto,
                    })
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
            return render(request, 'inscripto_exito.html', {'inscripto': inscripto, })
    return render(request, "inscripcion_social.html", {
        'titulo': "Inscribite", 
        'form': form, 
        'boton': "Inscribirse",
        'areas': areas,
        'dispositivos': dispositivos,
    })

def ver_inscripto(request, inscripcion_id, num_doc):
    try:
        inscripto = Inscripcion.objects.select_related('individuo', 'individuo__domicilio_actual', 'individuo__domicilio_actual__localidad')
        inscripto = inscripto.prefetch_related('tareas', 'tareas__tarea')
        inscripto = inscripto.prefetch_related('capacitaciones')
        inscripto = inscripto.get(pk=inscripcion_id, individuo__num_doc=num_doc)
        if inscripto.tipo_inscripto == 'PS':
            return render(request, 'panel_salud.html', {'inscripto': inscripto, })
        elif inscripto.tipo_inscripto == 'VS':
            inscripto.chequear_estado()
            return render(request, 'panel_social.html', {
                'inscripto': inscripto, 
                'capacitaciones': Capacitacion.objects.filter(tipo=inscripto.tipo_inscripto),
                'ubicaciones': Ubicacion.objects.filter(tipo='AP'),
            })
    except Inscripcion.DoesNotExist:
        return render(request, 'extras/error.html', {
            'titulo': 'Inscripcion Inexistente',
            'error': "En caso de que este sea el link que le llego a su correo por favor contacte a la administracion.",
        })

def subir_foto(request, inscripcion_id):
    form = UploadFoto()
    if request.method == "POST":
        form = UploadFoto(request.POST, request.FILES)
        if form.is_valid():
            inscripto = Inscripcion.objects.get(pk=inscripcion_id)
            inscripto.individuo.fotografia = form.cleaned_data['imagen']
            inscripto.individuo.save()
            return redirect('inscripciones:ver_inscripto', inscripcion_id=inscripcion_id, num_doc=inscripto.individuo.num_doc)
    return render(request, "extras/generic_form.html", {'titulo': "Subir Fotografia", 'form': form, 'boton': "Cargar", })

def cargar_frente_dni(request, inscripcion_id):
    form = UploadFoto()
    if request.method == "POST":
        form = UploadFoto(request.POST, request.FILES)
        if form.is_valid():
            inscripto = Inscripcion.objects.get(pk=inscripcion_id)
            individuo = inscripto.individuo
            #Creamos doc:
            documento = Documento(individuo=individuo)
            documento.tipo = 'DI'
            documento.archivo = form.cleaned_data['imagen']
            documento.aclaracion = 'FRENTE'
            documento.save()
            #Volvemos al panel
            return redirect('inscripciones:ver_inscripto', inscripcion_id=inscripcion_id, num_doc=inscripto.individuo.num_doc)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Foto del Frente del Documento", 'form': form, 'boton': "Cargar", })

def cargar_reverso_dni(request, inscripcion_id):
    form = UploadFoto()
    if request.method == "POST":
        form = UploadFoto(request.POST, request.FILES)
        if form.is_valid():
            inscripto = Inscripcion.objects.get(pk=inscripcion_id)
            individuo = inscripto.individuo
            #Creamos doc:
            documento = Documento(individuo=individuo)
            documento.tipo = 'DI'
            documento.archivo = form.cleaned_data['imagen']
            documento.aclaracion = 'REVERSO'
            documento.save()
            #Volvemos al panel
            return redirect('inscripciones:ver_inscripto', inscripcion_id=inscripcion_id, num_doc=inscripto.individuo.num_doc)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Foto del Reverso del Documento", 'form': form, 'boton': "Cargar", })

def ver_capacitacion(request, inscripto_id, capacitacion_id):
    #Obtenemos ambos objetos
    inscripto = Inscripcion.objects.get(pk=inscripto_id)
    capacitacion = Capacitacion.objects.get(id=capacitacion_id)
    #chequeamos que haya visto el anterior
    #Marcamos como vista la capacitacion
    inscripto.capacitaciones.add(capacitacion)
    #Generamos el link de la misma
    return redirect(capacitacion.link)

@permission_required('operadores.menu_inscripciones')
def editar_turnos(request, ubicacion_id):
    #Obtenemos la ubicacion
    ubicacion = Ubicacion.objects.prefetch_related('turnos_inscripciones')
    ubicacion = ubicacion.get(pk=ubicacion_id)
    #Generamos turnos
    dias = [timezone.now().date() + timedelta(days=x) for x in range(1,5)]
    turnos = []
    for dia in dias:#Por cada uno de los dias
        if dia.weekday() < 5:#si es laborable
            temp_fecha = datetime.combine(dia, ubicacion.hora_inicio)#Empezamos desde el primer momento del dia
            while temp_fecha.time() < ubicacion.hora_cierre:#
                #Chequeamos la cantidad de turnos sacados:
                ocupados = ubicacion.turnos_inscripciones.filter(fecha=temp_fecha).count()
                #Por que carajo no anda: 
                # ocupados = sum([1 for t in ubicacion.turnos_inscripciones.all() if t.fecha == temp_fecha])
                # Pero si anda: 
                # ocupados = sum([1 for t in ubicacion.turnos_inscripciones.filter(fecha==temp_fecha)])
                if ubicacion.capacidad_maxima > ocupados:
                    turnos.append([temp_fecha.strftime("%Y-%m-%d"), temp_fecha.strftime("%H:%M"), ubicacion.capacidad_maxima - ocupados])
                #Agregamos 20minutos
                temp_fecha += timedelta(minutes=ubicacion.duracion_turno)
    #Tenemos el bloque completo de turnos disponibles
    return render(request, "editar_turnero.html", {
        'ubicacion': ubicacion,
        'turnos': turnos, 
    })

@permission_required('operadores.menu_inscripciones')
def bajar_turno(request, ubicacion_id, fecha=None, hora=None):
    turno = Turno()
    turno.ubicacion = Ubicacion.objects.get(pk=ubicacion_id)
    turno.fecha = parse_datetime(fecha + ' ' + hora)#super bizzarre tool
    for x in range(0, turno.ubicacion.capacidad_maxima):
        turno.save()
        turno.pk = None
    return redirect('inscripciones:editar_turnos', ubicacion_id=turno.ubicacion.id)

def turnero(request, ubicacion_id, inscripto_id, fecha=None, hora=None):
    #Obtenemos el inscripto
    inscripto = Inscripcion.objects.select_related('individuo')
    inscripto = inscripto.get(pk=inscripto_id)
    #Obtenemos la ubicacion
    ubicacion = Ubicacion.objects.prefetch_related('turnos_inscripciones')
    ubicacion = ubicacion.get(pk=ubicacion_id)
    if not fecha:#Si no selecciono ninguna
        #Generamos turnos
        dias = [timezone.now().date() + timedelta(days=x) for x in range(1,5)]
        turnos = []
        for dia in dias:#Por cada uno de los dias
            if dia.weekday() < 5:#si es laborable
                temp_fecha = datetime.combine(dia, ubicacion.hora_inicio)#Empezamos desde el primer momento del dia
                while temp_fecha.time() < ubicacion.hora_cierre:#
                    #Chequeamos la cantidad de turnos sacados:
                    ocupados = ubicacion.turnos_inscripciones.filter(fecha=temp_fecha).count()
                    if ubicacion.capacidad_maxima > ocupados:
                        turnos.append([temp_fecha.strftime("%Y-%m-%d"), temp_fecha.strftime("%H:%M"), ubicacion.capacidad_maxima - ocupados])
                    #Agregamos 20minutos
                    temp_fecha += timedelta(minutes=ubicacion.duracion_turno)
        #Tenemos el bloque completo de turnos disponibles
        return render(request, "elegir_turno.html", {
            'inscripto': inscripto,
            'ubicacion': ubicacion,
            'turnos': turnos, 
        })
    else:  #  Si selecciono una fecha
        #Creamos el turno
        turno = Turno()
        turno.ubicacion = ubicacion
        turno.fecha = parse_datetime(fecha + ' ' + hora)#super bizzarre tool
        turno.inscripto = inscripto
        turno.save()
        #Volvemos al panel
        return redirect('inscripciones:ver_inscripto', inscripcion_id=inscripto.id, num_doc=inscripto.individuo.num_doc)

#Administracion
@permission_required('operadores.menu_inscripciones')
def menu(request):
    return render(request, 'menu_inscripciones.html', {})

@permission_required('operadores.menu_inscripciones')
def lista_voluntarios(request, tipo_inscripto):
    inscriptos = Inscripcion.objects.filter(disponible=True, tipo_inscripto=tipo_inscripto)
    inscriptos = inscriptos.select_related('individuo', 'individuo__domicilio_actual', 'individuo__domicilio_actual__localidad')
    #Definimos template segun tipo
    if tipo_inscripto == 'PS':
        template = 'lista_inscripciones_salud.html'
    elif tipo_inscripto == 'VS':
        template = 'lista_inscripciones_social.html'
    #Lanzamos template
    return render(request, template, 
        {
            'inscriptos': inscriptos,
            'has_table': True,
        }
    )

@permission_required('operadores.menu_inscripciones')
def lista_por_tarea(request, tarea_id):
    inscriptos = Inscripcion.objects.filter(disponible=True, tareas__tarea__id=tarea_id)
    inscriptos = inscriptos.select_related('individuo', 'individuo__domicilio_actual', 'individuo__domicilio_actual__localidad')
    return render(request, 'lista_inscripciones_social.html', 
        {
            'inscriptos': inscriptos,
            'has_table': True,
        }
    )

@permission_required('operadores.menu_inscripciones')
def lista_tareas(request):
    areas = Area.objects.all()
    return render(request, "lista_tareas.html", {
        'areas': areas,
    })

@permission_required('operadores.permisos')
def enviar_email(request, inscripcion_id):
    inscripto = Inscripcion.objects.select_related('individuo').get(pk=inscripcion_id)
    form = EmailForm(initial={'destinatario': inscripto.individuo.email})
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            if SEND_MAIL:
                to_email = form.cleaned_data['destinatario']
                #Preparamos el correo electronico
                mail_subject = form.cleaned_data['asunto']
                message = render_to_string('emails/inscripto_contacto.html', {
                        'inscripto': inscripto,
                        'cuerpo': form.cleaned_data['cuerpo'],
                    })
                #Guardamos el mail
                EmailsInscripto(inscripto=inscripto, asunto=mail_subject, cuerpo=form.cleaned_data['cuerpo'], operador=obtener_operador(request)).save()
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
        return redirect('inscripciones:ver_inscripto', inscripcion_id=inscripcion_id, num_doc=inscripto.individuo.num_doc)
    return render(request, "extras/generic_form.html", {'titulo': "Enviar Correo Electronico", 'form': form, 'boton': "Enviar", })

@permission_required('operadores.menu_inscripciones')
def avanzar_estado(request, inscripcion_id):
    inscripto = Inscripcion.objects.get(pk=inscripcion_id)
    if inscripto.estado < 4:
        inscripto.estado += 1
        inscripto.save()
    if inscripto.estado == 3:#Si termino la capacitacion
        if SEND_MAIL:
            to_email = inscripto.individuo.email
            mail_subject = 'COE2020 - Inscripcion Pre-Aprobada'
            #Preparamos el correo electronico
            mail_subject = 'COE2020 - Inscripcion Pre-Aprobada'
            message = render_to_string('emails/social_capacitacion.html', {
                    'inscripto': inscripto,
                })
            #Instanciamos el objeto mail con destinatario
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
    if inscripto.estado == 4:#Si termino el proceso
        #Le asignamos atributo de Voluntario Aprobado
        atributo = Atributo(individuo=inscripto.individuo)
        atributo.tipo = 'VA'
        atributo.aclaracion = "Aprobado por: " + str(obtener_operador(request))
        atributo.save()
        #Enviamos mail de aprobacion:
        if SEND_MAIL:
            to_email = inscripto.individuo.email
            #Preparamos el correo electronico
            mail_subject = 'COE2020 - Inscripcion Aprobada'
            message = render_to_string('emails/social_aprobada.html', {
                    'inscripto': inscripto,
                })
            #Instanciamos el objeto mail con destinatario
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
    return redirect('inscripciones:ver_inscripto', inscripcion_id=inscripcion_id, num_doc=inscripto.individuo.num_doc)

@permission_required('operadores.menu_inscripciones')
def download_inscriptos(request):
    inscriptos = Inscripcion.objects.all()
    #Iniciamos la creacion del csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Inscriptos.csv"'
    writer = csv.writer(response)
    writer.writerow(['REPORTE DE INSCRIPTOS'])
    writer.writerow(['FECHA:', timezone.now()])
    writer.writerow(['ID', 'TIPO_DOC', 'NUM_DOC', 'APELLIDOS', 'NOMBRES', 'PROFESION', 'MATRÍCULA', 'EMAIL', 'TELEFONO', 'INFO_EXTRA', 'VALIDO'])
    for item in inscriptos:
        writer.writerow([
            item.id,
            item.get_tipo_doc_display(),
            item.num_doc,
            item.apellidos,
            item.nombres,
            item.get_profesion_display(),
            item.matricula,
            item.email,
            item.telefono,
            delete_tags(item.info_extra),
            item.valido,
        ])
    #Enviamos el archivo para descargar
    return response

#Activar:
def activar_inscripcion(request, inscripcion_id, num_doc):
    try:
        inscripto = Inscripcion.objects.get(pk=inscripcion_id)
        inscripto.valido = True
        inscripto.save()
        return redirect('inscripciones:ver_inscripto', inscripcion_id=inscripto.id, num_doc=inscripto.individuo.num_doc)
    except(TypeError, ValueError, OverflowError, Inscripcion.DoesNotExist):
        texto = 'El link de activacion es invalido!'
    return render(request, 'extras/resultado.html', {'texto': texto, })

#Proyecto Estudiantil
def inscripcion_proyecto(request, token=None):
    proyecto = None
    if token:
        proyecto = ProyectoEstudiantil.objects.get(token=token)
    form = ProyectoEstudiantilForm(instance=proyecto)
    if request.method == "POST":
        form = ProyectoEstudiantilForm(request.POST, request.FILES, instance=proyecto)
        if form.is_valid():
            proyecto = form.save()
            if SEND_MAIL:
                to_email = proyecto.email_contacto
                #Preparamos el correo electronico
                mail_subject = "COE - Proyecto Estudiantil 2020"
                message = render_to_string('emails/acc_active_proyecto_estudiantil.html', {
                        'proyecto': proyecto,
                    })
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
            return redirect('inscripciones:panel_proyecto', token=proyecto.token)
    return render(request, "inscripcion_proyecto.html", {
        'titulo': "Inscribi tu Proyecto", 
        'form': form, 
        'boton': "Inscribirse",
    })

def panel_proyecto(request, token=None):
    proyecto = ProyectoEstudiantil.objects.select_related('responsable')
    proyecto = proyecto.prefetch_related('voluntarios')
    #Buscamos el proyecto
    proyecto = proyecto.get(token=token)
    #Lanzamos panel
    return render(request, "panel_proyecto.html", {'proyecto': proyecto})

@permission_required('operadores.menu_inscripciones')
def lista_proyectos(request):
    proyectos = ProyectoEstudiantil.objects.all()
    #Filtro
    #Optimizacion
    proyectos = proyectos.select_related('responsable')
    proyectos = proyectos.prefetch_related('voluntarios')
    #Lanzamos listado
    return render(request, "lista_proyectos.html", {
        'proyectos': proyectos,
        'has_table': True,
    })


def cargar_archivo_proyecto(request, token=None):
    form = FileForm()
    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            proyecto = ProyectoEstudiantil.objects.get(token=token)
            proyecto.documento = form.cleaned_data['archivo']
            proyecto.save()
            return redirect('inscripciones:panel_proyecto', token=proyecto.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Aval Institucional", 'form': form, 'boton': "Cargar", })

def cargar_aval_institucional(request, token=None):
    form = UploadFoto()
    if request.method == "POST":
        form = UploadFoto(request.POST, request.FILES)
        if form.is_valid():
            proyecto = ProyectoEstudiantil.objects.get(token=token)
            proyecto.escuela_aval = form.cleaned_data['imagen']
            proyecto.save()
            return redirect('inscripciones:panel_proyecto', token=proyecto.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Aval Institucional", 'form': form, 'boton': "Cargar", })

def cargar_responsable_institucional(request, token=None, individuo_id=None):
    if individuo_id:
        individuo = Individuo.objects.get(pk=individuo_id)
        form = IndividuoForm(instance=individuo,
                    initial={
                        'dom_localidad': individuo.domicilio_actual.localidad,
                        'dom_calle': individuo.domicilio_actual.calle,
                        'dom_numero': individuo.domicilio_actual.numero,
                        'dom_aclaracion': individuo.domicilio_actual.aclaracion,
                        'frente_dni': getattr(individuo.documentos.filter(tipo='DI', aclaracion='Frente').last(), 'archivo', None),
                        'reverso_dni': getattr(individuo.documentos.filter(tipo='DI', aclaracion='Reverso').last(), 'archivo', None),
                    })
    else:
        form = IndividuoForm()
    if request.method == "POST":
        #obtenemos ingreso
        proyecto = ProyectoEstudiantil.objects.get(token=token)
        try:#Tratamos de obtener el dni
            num_doc = request.POST['num_doc']
            individuo = Individuo.objects.get(num_doc=num_doc)
        except Individuo.DoesNotExist:
            individuo = None
        form = IndividuoForm(request.POST, request.FILES, instance=individuo)
        if form.is_valid():
            #actualizamos individuo con los datos nuevos
            individuo = actualizar_individuo(form)
            #Le agregamos el atributo de Educacion >>> SOLO SI ESTA APROBADO
            #Atributo.objects.filter(individuo=individuo, tipo='EP').delete()
            #atributo = Atributo(individuo=individuo)
            #atributo.tipo = 'EP'
            #atributo.aclaracion = 'Docente de ' + proyecto.escuela_nombre
            #atributo.save()
            #Agregamos el responsable:
            proyecto.responsable = individuo
            proyecto.save()
            return redirect('inscripciones:panel_proyecto', token=proyecto.token)
    return render(request, "cargar_responsable.html", {'titulo': "Cargar Responsable Institucional", 'form': form, })

def cargar_voluntario(request, token, individuo_id=None):
    if individuo_id:
        individuo = Individuo.objects.get(pk=individuo_id)
        form = IndividuoForm(instance=individuo,
                    initial={
                        'dom_localidad': individuo.domicilio_actual.localidad,
                        'dom_calle': individuo.domicilio_actual.calle,
                        'dom_numero': individuo.domicilio_actual.numero,
                        'dom_aclaracion': individuo.domicilio_actual.aclaracion,
                        'frente_dni': getattr(individuo.documentos.filter(tipo='DI', aclaracion='Frente').last(), 'archivo', None),
                        'reverso_dni': getattr(individuo.documentos.filter(tipo='DI', aclaracion='Reverso').last(), 'archivo', None),
                    })
    else:
        form = IndividuoForm()
    if request.method == "POST":
        #obtenemos ingreso
        proyecto = ProyectoEstudiantil.objects.get(token=token)
        try:#Tratamos de obtener el dni
            num_doc = request.POST['num_doc']
            individuo = Individuo.objects.get(num_doc=num_doc)
        except Individuo.DoesNotExist:
            individuo = None
        form = IndividuoForm(request.POST, request.FILES, instance=individuo)
        if form.is_valid():
            #actualizamos individuo con los datos nuevos
            individuo = actualizar_individuo(form)
            #Agregamos el voluntario:
            proyecto.voluntarios.add(individuo)
            proyecto.save()
            return redirect('inscripciones:panel_proyecto', token=proyecto.token)
    return render(request, "cargar_voluntario.html", {'titulo': "Cargar Voluntario", 'form': form, })

def quitar_voluntario_proyecto(request, token, individuo_id):
    proyecto = ProyectoEstudiantil.objects.get(token=token)
    individuo = Individuo.objects.get(pk=individuo_id)
    proyecto.voluntarios.remove(individuo)
    return redirect('inscripciones:panel_proyecto', token=proyecto.token)

def cargar_tutor(request, token, voluntario_id):
    voluntario = Individuo.objects.get(pk=voluntario_id)
    form = IndividuoForm()
    if request.method == "POST":
        #obtenemos ingreso
        proyecto = ProyectoEstudiantil.objects.get(token=token)
        try:#Tratamos de obtener el dni del tutor
            num_doc = request.POST['num_doc']
            tutor = Individuo.objects.get(num_doc=num_doc)
        except Individuo.DoesNotExist:
            tutor = None
        form = IndividuoForm(request.POST, request.FILES, instance=tutor)
        if form.is_valid():
            #actualizamos individuo con los datos nuevos
            tutor = actualizar_individuo(form)
            #Agregamos relacion con voluntario
            relacion = Relacion(tipo='F')
            relacion.individuo = voluntario
            relacion.relacionado = tutor
            relacion.aclaracion = "Tutor informado para Proyecto Estudiantil"
            relacion.save()
            #Lanzamos panel
            return redirect('inscripciones:panel_proyecto', token=proyecto.token)
    return render(request, "cargar_tutor.html", {'titulo': "Cargar Tutor", 'form': form, 'voluntario': voluntario, })

def cargar_autorizacion(request, token, voluntario_id):
    form = UploadFoto()
    if request.method == "POST":
        form = UploadFoto(request.POST, request.FILES)
        if form.is_valid():
            proyecto = ProyectoEstudiantil.objects.get(token=token)
            voluntario = Individuo.objects.get(pk=voluntario_id)
            #Cargamos el documento
            doc = Documento(individuo=voluntario)
            doc.tipo = 'AT'
            doc.archivo = form.cleaned_data['imagen']
            doc.aclaracion = "Para Proyecto: " + proyecto.nombre
            doc.save()
            return redirect('inscripciones:panel_proyecto', token=proyecto.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Aval Institucional", 'form': form, 'boton': "Cargar", })

#Sistema COCA
def pedir_coca(request):
    return render(request, "pedir_coca.html", {'title': "Sistema de Provisión de Coca", })

def peticion_persona(request, peticionp_id=None):
    peticionp = None
    if peticionp_id:
        peticionp = Peticionp.objects.get(pk=peticionp_id)
    form = PeticionpForm(instance=peticionp)
    if request.method == "POST":
        form = PeticionpForm(request.POST, instance=peticionp)
        if form.is_valid():
            peticionp = form.save()
            #Enviar email
            if SEND_MAIL:
                to_email = peticionp.email_contacto
                #Preparamos el correo electronico
                mail_subject = 'COE2020 Petición de COCA Jujuy!'
                message = render_to_string('emails/email_persona_pet.html', {
                    'peticion': peticionp,
                })
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
            #Enviarlo a cargar ingresantes
            return redirect('inscripciones:ver_peticion_persona', token=peticionp.token)
        else: 
            return render(request, "peticion_persona.html", {
                'title': "PETICIÓN DE COCA - PERSONAS", 
                'form': form, 
                'button': "Iniciar Pedido",
                'message': 'FORMULARIO INVÁLIDO, CORRIJA DATOS.' 
            })
    return render(request, "peticion_persona.html", {'title': "PETICIÓN DE COCA - PERSONAS", 'form': form, 'button': "Iniciar Pedido", })

def ver_peticion_persona(request, token):
    peticionp = Peticionp.objects.prefetch_related('individuos')
    peticionp = peticionp.get(token=token)
    #Calcular Limite para eliminacion
    limite = int(72 - (timezone.now() - peticionp.fecha).total_seconds() / 3600)
    return render(request, 'panel_peticion.html', {
        'peticionp': peticionp,
        'limite': limite,        
        'has_table': True,
    })

def cargar_people(request, peticionp_id, individuo_id=None):
    individuo = None
    if individuo_id:
        individuo = Individuo.objects.get(pk=individuo_id)
    form = PersonapForm(instance=individuo)
    if request.method == "POST":
        #obtenemos peticion
        peticionp = Peticionp.objects.get(pk=peticionp_id)
        try:#Tratamos de obtener el dni
            num_doc = request.POST['num_doc']
            individuo = Individuo.objects.get(num_doc=num_doc)
        except Individuo.DoesNotExist:
            individuo = None
        form = PersonapForm(request.POST, request.FILES, instance=individuo)
        if form.is_valid():
            #actualizamos individuo con los datos nuevos
            individuo = actualizar_individuo(form)            
            individuo.destino = peticionp.destino
            individuo.save()
            #Lo agregamos al registro
            peticionp.individuos.add(individuo)
            return redirect('inscripciones:ver_peticion_persona', token=peticionp.token)
    return render(request, "cargar_people.html", {'title': "Cargar Datos Personales", 'form': form, 'button': "Cargar", }) 

def quitar_persona(request, peticionp_id, individuo_id):
    peticionp = Peticionp.objects.get(pk=peticionp_id)
    individuo = Individuo.objects.get(pk=individuo_id)
    peticionp.individuos.remove(individuo)
    return redirect('inscripciones:ver_peticion_persona', token=peticionp.token)

def finalizar_peticion(request, peticionp_id):
    peticionp = Peticionp.objects.get(pk=peticionp_id)    
    #Chequear que el ingreso este finalizado
    if not peticionp.individuos.exists():
        return render(request, 'extras/error.html', {
            'titulo': 'FINALIZACIÓN DEGENEGADA',
            'error': "USTED DEBE CARGAR SUS DATOS PERSONALES",
        })    
    #Pasar a estado finalizado    
    peticionp.estado = 'E'
    peticionp.save()
    return redirect('inscripciones:ver_peticion_persona', token=peticionp.token)

#Administrar
@permission_required('operadores.menu_provisiones')
def lista_peticiones(request, estado=None):
    peticionp = Peticionp.objects.all()
    #Filtramos de ser necesario
    if not estado:
        peticionp = peticionp.exclude(estado='B')
    if estado:
        peticionp = peticionp.filter(estado=estado)
    #Optimizamos
    peticionp = peticionp.select_related('destino', 'operador')
    peticionp = peticionp.prefetch_related('individuos')
    #Lanzamos listado
    return render(request, 'lista_peticiones.html', {
        'title': "Ingresos Pedidos",
        'peticionp': peticionp,
        'has_table': True,
    })

@permission_required('operadores.menu_provisiones')
def lista_peticiones_completas(request):
    peticionp = Peticionp.objects.filter(estado='E')    
    #Optimizamos
    peticionp = peticionp.select_related('destino', 'operador')
    peticionp = peticionp.prefetch_related('individuos', 'individuos__domicilio_actual', 'individuos__domicilio_actual__localidad')
    peticionp = peticionp.prefetch_related('individuos__documentos')
    #Lanzamos listado
    return render(request, 'lista_peticiones.html', {
        'title': "Peticiones Completas Esperando Aprobacion",
        'peticionp': peticionp,
        'has_table': True,
    })

@permission_required('operadores.menu_provisiones')
def peticion_enviar_email(request, peticionp_id):
    peticionp = Peticionp.objects.get(pk=peticionp_id)
    form = EmailForm(initial={'destinatario': peticionp.email_contacto})
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            if SEND_MAIL:
                to_email = form.cleaned_data['destinatario']
                #Preparamos el correo electronico
                mail_subject = form.cleaned_data['asunto']
                message = render_to_string('emails/ingreso_contacto.html', {
                        'peticionp': peticionp,
                        'cuerpo': form.cleaned_data['cuerpo'],
                    })
                #Guardamos el mail
                Emails_Peticionp(peticionp=peticionp, asunto=mail_subject, cuerpo=form.cleaned_data['cuerpo'], operador=obtener_operador(request)).save()
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
        return redirect('inscripciones:ver_peticion_persona', token=peticionp.token)
    return render(request, "extras/generic_form.html", {'titulo': "Enviar Correo Electronico", 'form': form, 'boton': "Enviar", })

@permission_required('operadores.menu_inscripciones')
def peticion_enviado(request, peticionp_id):
    peticionp = Peticionp.objects.get(pk=peticionp_id)
    peticionp.estado = 'N'
    peticionp.save()
    return redirect('inscripciones:ver_peticion_persona', token=peticionp.token)

@permission_required('operadores.menu_inscripciones')
def eliminar_peticion(request, peticionp_id):
    peticionp = Peticionp.objects.get(pk=peticionp_id)
    peticionp.estado = 'B'
    peticionp.operador = obtener_operador(request)
    peticionp.save()
    return redirect('inscripciones:lista_peticiones')

#Peticiones Organización           

def peticion_organizacion(request, organizacion_id=None):  
    organizacion = None
    if organizacion_id:
        organizacion = Organization.objects.get(pk=organizacion_id)
        form = OrganizationForm(instance=organizacion)
        domicilio = DomicilioOrganizacion.objects.get(organizacion_id=organizacion_id)
        if domicilio:
            form = OrganizationForm(
                instance = organizacion,
                initial={
                    'localidad': domicilio.localidad,
                    'barrio': domicilio.barrio,
                    'calle': domicilio.calle,
                    'numero': domicilio.numero,
                    'manzana': domicilio.manzana,
                    'lote': domicilio.lote,
                    'piso': domicilio.piso,
                }
            )
        if request.method == "POST":
            form = OrganizationForm(request.POST, request.FILES, instance=organizacion)
            if form.is_valid():
                organizacion = form.save(commit=False)
                organizacion.save()
                #Generamos modelos externos:
                if form.cleaned_data['localidad']:                    
                    domicilio.organizacion = organizacion
                    domicilio.localidad = form.cleaned_data['localidad']
                    domicilio.barrio = form.cleaned_data['barrio']
                    domicilio.calle = form.cleaned_data['calle']
                    domicilio.numero = form.cleaned_data['numero']
                    domicilio.manzana = form.cleaned_data['manzana']
                    domicilio.lote = form.cleaned_data['lote']
                    domicilio.piso = form.cleaned_data['piso']
                    domicilio.save()                    
                return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)
            else: 
                return render(request, "peticion_organizacion.html", {
                    'title': "PETICIÓN DE COCA - ORGANIZACION", 
                    'form': form, 
                    'button': "Iniciar Pedido",
                    'message': 'FORMULARIO INVÁLIDO, CORRIJA DATOS.' 
                })
    else:
        form = OrganizationForm()
        if request.method == "POST":
            form = OrganizationForm(request.POST, request.FILES)
            if form.is_valid():
                organizacion = form.save(commit=False)
                organizacion.save()
                #Creamos Domicilio
                domicilio = DomicilioOrganizacion()
                domicilio.organizacion = organizacion
                if form.cleaned_data['localidad']:
                    domicilio.localidad = form.cleaned_data['localidad']
                    domicilio.barrio = form.cleaned_data['barrio']
                    domicilio.calle = form.cleaned_data['calle']
                    domicilio.numero = form.cleaned_data['numero']
                    domicilio.manzana = form.cleaned_data['manzana']
                    domicilio.lote = form.cleaned_data['lote']
                    domicilio.piso = form.cleaned_data['piso']
                    domicilio.save()            
                #Enviar email
                if SEND_MAIL:
                    to_email = organizacion.mail_institucional
                    #Preparamos el correo electronico
                    mail_subject = 'COE2020 Petición de COCA Jujuy!'
                    message = render_to_string('emails/email_org_pet.html', {
                    'organizacion': organizacion,
                    })
                    #Instanciamos el objeto mail con destinatario
                    email = EmailMessage(mail_subject, message, to=[to_email])
                    email.send()
                #Enviarlo a cargar ingresantes
                return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)
            else: 
                return render(request, "peticion_organizacion.html", {
                    'title': "PETICIÓN DE COCA - ORGANIZACION", 
                    'form': form, 
                    'button': "Iniciar Pedido",
                    'message': 'FORMULARIO INVÁLIDO, CORRIJA DATOS.' 
                })
    return render(request, "peticion_organizacion.html", {'title': "PETICIÓN DE COCA - ORGANIZACIONES", 'form': form, 'button': "Iniciar Pedido", })

def ver_peticion_organizacion(request, token):
    organizacion = Organization.objects.prefetch_related('responsables', 'empleados')    
    organizacion = organizacion.get(token=token)
    domicilio = DomicilioOrganizacion.objects.get(organizacion = organizacion)
    #Calcular Limite para eliminacion
    limite = int(72 - (timezone.now() - organizacion.fecha).total_seconds() / 3600)
    return render(request, 'panel_peticion_org.html', {
        'organizacion': organizacion,
        'domicilio': domicilio,
        'limite': limite,        
        'has_table': True,
    })
    

def cargar_responsable_org(request, organizacion_id, responsable_id=None):
    responsable = None
    if responsable_id:
        responsable = Responsable.objects.get(pk=responsable_id) 
        form = ResponsableForm(instance=responsable)
        if request.method == "POST":
            #obtenemos peticion
            organizacion = Organization.objects.get(pk=organizacion_id)        
            form = ResponsableForm(request.POST, instance=responsable)
            if form.is_valid():
                responsable = form.save(commit=False)
                #Guardamos los datos del responsable y lo vinculamos a la organizacion                      
                responsable.save()
                #Lo agregamos al registro
                organizacion.responsables.add(responsable)            
                return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)
            else:
                return render(request, "cargar_responsable_org.html", {
                    'title': "Cargar Datos del Responsable", 
                    'form': form, 
                    'button': "Cargar", 
                    'message': 'Formulario inválido', 
                })
    else:
        form = ResponsableForm()
        if request.method == "POST":
            #obtenemos peticion
            organizacion = Organization.objects.get(pk=organizacion_id)        
            form = ResponsableForm(request.POST)
            if form.is_valid():
                responsable = form.save(commit=False)
                #Guardamos los datos del responsable y lo vinculamos a la organizacion                      
                responsable.save()
                #Lo agregamos al registro
                organizacion.responsables.add(responsable)            
                return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)
            else:
                return render(request, "cargar_responsable_org.html", {
                    'title': "Cargar Datos del Responsable", 
                    'form': form, 
                    'button': "Cargar", 
                    'message': 'Formulario inválido', 
                })                
    return render(request, "cargar_responsable_org.html", {'title': "Cargar Datos del Responsable", 'form': form, 'button': "Cargar", })

def cargar_empleado_org(request, organizacion_id, empleado_id=None):
    empleado = None
    if empleado_id:
        empleado = Empleado.objects.get(pk=empleado_id) 
        form = EmpleadoForm(instance=empleado)
        if request.method == "POST":
            #obtenemos peticion
            organizacion = Organization.objects.get(pk=organizacion_id)        
            form = EmpleadoForm(request.POST, instance=empleado)
            if form.is_valid():
                empleado = form.save(commit=False)
                #Guardamos los datos del responsable y lo vinculamos a la organizacion                      
                empleado.save()
                #Lo agregamos al registro
                organizacion.empleados.add(empleado)            
                return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)
            else:
                return render(request, "cargar_empleado_org.html", {
                    'title': "Cargar Datos del Empleado", 
                    'form': form, 
                    'button': "Cargar", 
                    'message': 'Formulario inválido', 
                })
    else:
        form = EmpleadoForm()
        if request.method == "POST":
            #obtenemos peticion
            organizacion = Organization.objects.get(pk=organizacion_id)        
            form = EmpleadoForm(request.POST)
            if form.is_valid():
                empleado = form.save(commit=False)
                #Guardamos los datos del responsable y lo vinculamos a la organizacion                      
                empleado.save()
                #Lo agregamos al registro
                organizacion.empleados.add(empleado)            
                return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)
            else:
                return render(request, "cargar_empleado_org.html", {
                    'title': "Cargar Datos del Empleado", 
                    'form': form, 
                    'button': "Cargar", 
                    'message': 'Formulario inválido', 
                })                
    return render(request, "cargar_empleado_org.html", {'title': "Cargar Datos del Empleado", 'form': form, 'button': "Cargar", })


def quitar_responsable_org(request, organizacion_id, responsable_id):
    organizacion = Organization.objects.get(pk=organizacion_id)
    responsable = Responsable.objects.get(pk=responsable_id)
    organizacion.responsables.remove(responsable)
    return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)

def quitar_empleado_org(request, organizacion_id, empleado_id):
    organizacion = Organization.objects.get(pk=organizacion_id)
    empleado = Empleado.objects.get(pk=empleado_id)
    organizacion.empleados.remove(empleado)
    return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)


def finalizar_peticion_org(request, organizacion_id):
    organizacion = Organization.objects.get(pk=organizacion_id)    
    #Chequear que el ingreso este finalizado
    if not organizacion.responsables.exists() or not organizacion.empleados.exists():
        return render(request, 'extras/error.html', {
            'titulo': 'FINALIZACIÓN DEGENEGADA',
            'error': "USTED DEBE CARGAR AL MENOS UN EMPLEADO Y EL RESPONSABLE DE LA INSTITUCIÓN",
        })    
    #Pasar a estado finalizado    
    organizacion.estado = 'E'
    organizacion.save()
    return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)

#Administrar COCA - ORGANIZACIONES
@permission_required('operadores.menu_inscripciones')
def lista_peticiones_org(request, estado=None):
    organizacion = Organization.objects.all()
    #Filtramos de ser necesario
    if not estado:
        organizacion = organizacion.exclude(estado='B')
    else:
        organizacion = organizacion.filter(estado=estado)
    #Optimizamos
    organizacion = organizacion.select_related('operador')
    organizacion = organizacion.prefetch_related('responsables')
    #Lanzamos listado
    return render(request, 'lista_peticiones_org.html', {
        'titulo': "Listado de Peticiones de Coca",
        'organizacion': organizacion,
        'has_table': True,
    })

@permission_required('operadores.menu_inscripciones')
def lista_peticiones_org_completas(request):
    organizacion = Organization.objects.filter(estado='E')    
    #Optimizamos
    #ingresos = ingresos.select_related('origen', 'destino', 'operador')
    #ingresos = ingresos.prefetch_related('individuos', 'individuos__domicilio_actual', 'individuos__domicilio_actual__localidad')
    #ingresos = ingresos.prefetch_related('individuos__documentos')
    #Lanzamos listado
    return render(request, 'lista_peticiones_org.htm', {
        'titulo': "Peticiones Completas Esperando Aprobacion",
        'organizacion': organizacion,
        'has_table': True,
    })


@permission_required('operadores.menu_inscripciones')
def peticion_org_enviar_email(request, organizacion_id):
    organizacion = Organization.objects.get(pk=organizacion_id)
    form = EmailForm(initial={'destinatario': organizacion.mail_institucional})
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            if SEND_MAIL:
                to_email = form.cleaned_data['destinatario']
                #Preparamos el correo electronico
                mail_subject = form.cleaned_data['asunto']
                message = render_to_string('emails/ingreso_contacto.html', {
                        'organizacion': organizacion,
                        'cuerpo': form.cleaned_data['cuerpo'],
                    })
                #Guardamos el mail
                Emails_Ingreso(organizacion=organizacion, asunto=mail_subject, cuerpo=form.cleaned_data['cuerpo'], operador=obtener_operador(request)).save()
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
        return redirect('inscripciones:ver_peticion_organizacion', token=organizacion.token)
    return render(request, "extras/generic_form.html", {'titulo': "Enviar Correo Electronico", 'form': form, 'boton': "Enviar", })

@permission_required('operadores.permisos')
def eliminar_peticion_org(request, organizacion_id):
    organizacion = Organization.objects.get(pk=organizacion_id)
    organizacion.estado = 'B'
    organizacion.operador = obtener_operador(request)
    organizacion.save()
    return redirect('inscripciones:lista_peticiones_org')