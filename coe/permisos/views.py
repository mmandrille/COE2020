#Imports de Python
import math
from datetime import timedelta
#Imports Django
from django.utils import timezone
from django.shortcuts import render
from django.shortcuts import redirect
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.contrib.auth.decorators import permission_required
#Imports extras
#Imports del proyecto
from coe.settings import SEND_MAIL
from core.decoradores import superuser_required
from core.forms import EmailForm, UploadFoto
from core.functions import date2str
from operadores.functions import obtener_operador
from informacion.models import Individuo, Atributo
from informacion.functions import actualizar_individuo
from graficos.functions import obtener_grafico
#imports de la app
from .choices import TIPO_INGRESO, ESTADO_INGRESO
from .models import NivelRestriccion, Permiso
from .models import IngresoProvincia, Emails_Ingreso
from .models import CirculacionTemporal, Emails_Circulacion
from .forms import NivelRestriccionForm
from .forms import PermisoForm, BuscarPermiso, DatosForm, FotoForm
from .forms import IngresoProvinciaForm, IngresanteForm, AprobarForm
from .forms import CirculacionTemporalForm
from .forms import DUTForm, PlanVueloForm
from .functions import buscar_permiso, validar_permiso

#Publico
def buscar_permiso_web(request):
    form = BuscarPermiso()
    if request.method == 'POST':
        form = BuscarPermiso(request.POST)
        if form.is_valid():
            individuo = Individuo.objects.filter(
                num_doc=form.cleaned_data['num_doc'],
                apellidos__icontains=form.cleaned_data['apellido'])
            if individuo:
                individuo = individuo.first()
                return redirect('permisos:pedir_permiso', individuo_id=individuo.id, num_doc=individuo.num_doc)
            else:
                form.add_error(None, "No se ha encontrado a Nadie con esos Datos.")
    return render(request, "buscar_permiso.html", {'form': form, })

def pedir_permiso_web(request, individuo_id, num_doc):
    try:
        individuo = Individuo.objects.get(pk=individuo_id, num_doc=num_doc)
        form = PermisoForm(initial={'individuo': individuo, })
        if request.method == 'POST':
            form = PermisoForm(request.POST, initial={'individuo': individuo, })
            if form.is_valid():
                permiso = buscar_permiso(individuo)
                if not permiso.pk:#Si el permiso aun no fue guardado:
                    permiso = form.save(commit=False)#Vamos a procesar el requerimiento
                    permiso.individuo = individuo
                    permiso = validar_permiso(individuo, permiso)
                    if permiso.aprobar:
                        permiso.save()
                        #Enviar email
                        if SEND_MAIL:
                            to_email = individuo.email
                            #Preparamos el correo electronico
                            mail_subject = 'COE2020 Permiso Digital Aprobado'
                            message = render_to_string('emails/permiso_generado.html', {
                                    'individuo': individuo,
                                    'permiso': permiso,
                                })
                            #Instanciamos el objeto mail con destinatario
                            email = EmailMessage(mail_subject, message, to=[to_email])
                            email.send()
                return render(request, "ver_permiso.html", {'permiso': permiso, })  
        return render(request, "pedir_permiso.html", {'form': form, 'individuo': individuo, })
    except Individuo.DoesNotExist:
        return redirect('permisos:buscar_permiso')

def completar_datos(request, individuo_id):
    individuo = Individuo.objects.get(pk=individuo_id)
    form = DatosForm(instance=individuo)
    if request.method == "POST":
        form = DatosForm(request.POST, instance=individuo)
        if form.is_valid():
            form.save()
            return redirect('permisos:pedir_permiso', individuo_id=individuo.id, num_doc=individuo.num_doc)
    return render(request, "extras/generic_form.html", {'titulo': "Corregir/Completar Datos", 'form': form, 'boton': "Guardar", })

def subir_foto(request, individuo_id):
    individuo = Individuo.objects.get(pk=individuo_id)
    form = FotoForm()
    if request.method == "POST":
        form = FotoForm(request.POST, request.FILES)
        if form.is_valid():
            individuo.fotografia = form.cleaned_data['fotografia']
            individuo.save()
            return redirect('permisos:pedir_permiso', individuo_id=individuo.id, num_doc=individuo.num_doc)
    return render(request, "extras/generic_form.html", {'titulo': "Subir Fotografia", 'form': form, 'boton': "Cargar", })

#Ingreso Provincial
def pedir_ingreso_provincial(request, ingreso_id=None):
    ingreso = None
    if ingreso_id:
        ingreso = IngresoProvincia.objects.get(pk=ingreso_id)
    form = IngresoProvinciaForm(instance=ingreso)
    if request.method == "POST":
        form = IngresoProvinciaForm(request.POST, request.FILES, instance=ingreso)
        if form.is_valid():
            ingreso = form.save()
            #Enviar email
            if SEND_MAIL:
                to_email = ingreso.email_contacto
                #Preparamos el correo electronico
                mail_subject = 'COE2020 Requerimiento de Ingreso Provincial Jujuy!'
                message = render_to_string('emails/ingreso_provincial.html', {
                    'ingreso': ingreso,
                })
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
            #Enviarlo a cargar ingresantes
            return redirect('permisos:ver_ingreso_provincial', token=ingreso.token)
    return render(request, "extras/generic_form.html", {'titulo': "Permiso de Ingreso a Jujuy", 'form': form, 'boton': "Cargar", })

def ver_ingreso_provincial(request, token):
    ingreso = IngresoProvincia.objects.prefetch_related('individuos')
    ingreso = ingreso.get(token=token)
    return render(request, 'ver_ingreso_provincial.html', {
        'ingreso': ingreso,
        'falta_app': ingreso.individuos.filter(appdata=None).exists(),
        'has_table': True,
    })

def cargar_ingresante(request, ingreso_id, individuo_id=None):
    individuo = None
    if individuo_id:
        individuo = Individuo.objects.get(pk=individuo_id)
    form = IngresanteForm(instance=individuo)
    if request.method == "POST":
        #obtenemos ingreso
        ingreso = IngresoProvincia.objects.get(pk=ingreso_id)
        try:#Tratamos de obtener el dni
            num_doc = request.POST['num_doc']
            individuo = Individuo.objects.get(num_doc=num_doc)
        except Individuo.DoesNotExist:
            individuo = None
        form = IngresanteForm(request.POST, instance=individuo)
        if form.is_valid():
            #actualizamos individuo con los datos nuevos
            individuo = actualizar_individuo(form)
            #individuo.origen = ingreso.origen
            individuo.destino = ingreso.destino
            individuo.save()
            #Lo agregamos al registro
            ingreso.individuos.add(individuo)
            return redirect('permisos:ver_ingreso_provincial', token=ingreso.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Ingresante", 'form': form, 'boton': "Cargar", })

def cargar_dut(request, ingreso_id):
    form = DUTForm()
    if request.method == "POST":
        #obtenemos ingreso
        ingreso = IngresoProvincia.objects.get(pk=ingreso_id)
        form = DUTForm(request.POST, request.FILES, instance=ingreso)
        if form.is_valid():
            form.save()
            return redirect('permisos:ver_ingreso_provincial', token=ingreso.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Documento Universal de Transporte", 'form': form, 'boton': "Cargar", })

def cargar_plan_vuelo(request, ingreso_id):
    form = PlanVueloForm()
    if request.method == "POST":
        #obtenemos ingreso
        ingreso = IngresoProvincia.objects.get(pk=ingreso_id)
        form = PlanVueloForm(request.POST, request.FILES, instance=ingreso)
        if form.is_valid():
            form.save()
            return redirect('permisos:ver_ingreso_provincial', token=ingreso.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Documento Universal de Transporte", 'form': form, 'boton': "Cargar", })

def quitar_ingresante(request, ingreso_id, individuo_id):
    ingreso = IngresoProvincia.objects.get(pk=ingreso_id)
    individuo = Individuo.objects.get(pk=individuo_id)
    ingreso.individuos.remove(individuo)
    return redirect('permisos:ver_ingreso_provincial', token=ingreso.token)

def finalizar_ingreso(request, ingreso_id):
    ingreso = IngresoProvincia.objects.get(pk=ingreso_id)
    #Chequear que el ingreso este finalizado
    if ingreso.tipo == 'P':#Particular
        if not ingreso.individuos.exists():
            return render(request, 'extras/error.html', {
            'titulo': 'Finalizacion Denegada',
            'error': "Usted debe informar TODOS los pasajeros del Vehiculo antes de terminar el Requerimiento.",
        })
    elif ingreso.tipo == 'C':#Colectivos
        if not ingreso.dut:
            return render(request, 'extras/error.html', {
            'titulo': 'Finalizacion Denegada',
            'error': "Usted debe Subir el Documento Universal de Transporte antes de terminar el requerimiento.",
        })
    elif ingreso.tipo == 'A':#Aereo
        if not ingreso.plan_vuelo:
            return render(request, 'extras/error.html', {
            'titulo': 'Finalizacion Denegada',
            'error': "Usted debe Subir el Plan de Vuelo Autorizado antes de terminar el requerimiento.",
        })
    #Pasar a estado finalizado
    ingreso.estado = 'E'
    ingreso.save()
    return redirect('permisos:ver_ingreso_provincial', token=ingreso.token)

def ver_ingreso_aprobado(request, token):
    ingreso = IngresoProvincia.objects.get(token=token)
    ingreso.generar_pdf()
    return HttpResponseRedirect('/archivos/permisos/'+ingreso.token+'.pdf')

#CIRCULACION
def pedir_circulacion_temporal(request, circulacion_id=None):
    circulacion = None
    if circulacion_id:
        circulacion = CirculacionTemporal.objects.get(pk=circulacion_id)
    form = CirculacionTemporalForm(instance=circulacion)
    if request.method == "POST":
        form = CirculacionTemporalForm(request.POST, request.FILES, instance=circulacion)
        if form.is_valid():
            circulacion = form.save()
            #Enviar email
            if SEND_MAIL:
                to_email = ingreso.email_contacto
                #Preparamos el correo electronico
                mail_subject = 'COE2020 Requerimiento de Circulacion Temporal - Provincial Jujuy!'
                message = render_to_string('emails/circulacion_temporal.html', {
                    'circulacion': circulacion,
                })
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
            #Enviarlo a cargar ingresantes
            return redirect('permisos:ver_circulacion_temporal', token=circulacion.token)
    return render(request, "extras/generic_form.html", {'titulo': "Permiso de Circulacion Temporal - Jujuy", 'form': form, 'boton': "Cargar", })

def ver_circulacion_temporal(request, token):
    #Optimizamos busqueda
    circulaciones = CirculacionTemporal.objects.select_related('chofer', 'acompañante')
    circulaciones = circulaciones.select_related('origen', 'destino')
    #Buscamos el indicado
    circulacion = circulaciones.get(token=token)
    #Mostramos panel
    return render(request, 'ver_circulacion_temporal.html', {
        'circulacion': circulacion,
    })

def circ_subir_permiso_nac(request, token):
    form = UploadFoto()
    if request.method == "POST":
        #obtenemos ingreso
        form = UploadFoto(request.POST, request.FILES)
        if form.is_valid():
            circulacion = CirculacionTemporal.objects.get(token=token)
            circulacion.permiso_nacional = form.cleaned_data['imagen']
            circulacion.save()
            return redirect('permisos:ver_circulacion_temporal', token=circulacion.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Permiso Nacional de Circulacion", 'form': form, 'boton': "Cargar", })

def circ_subir_licencia(request, token):
    form = UploadFoto()
    if request.method == "POST":
        #obtenemos ingreso
        form = UploadFoto(request.POST, request.FILES)
        if form.is_valid():
            circulacion = CirculacionTemporal.objects.get(token=token)
            circulacion.licencia_conducir = form.cleaned_data['imagen']
            #Podriamos agregar ese doc al individuo
            circulacion.save()
            return redirect('permisos:ver_circulacion_temporal', token=circulacion.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Permiso Nacional de Circulacion", 'form': form, 'boton': "Cargar", })

def circ_cargar_chofer(request, token, individuo_id=None):
    individuo = None
    if individuo_id:
        individuo = Individuo.objects.get(pk=individuo_id)
    form = IngresanteForm(instance=individuo)
    if request.method == "POST":
        #obtenemos ingreso
        form = IngresanteForm(request.POST, instance=individuo)
        if form.is_valid():
            circulacion = CirculacionTemporal.objects.get(token=token)
            #actualizamos individuo con los datos nuevos
            individuo = actualizar_individuo(form)
            #individuo.origen = circulacion.origen
            individuo.destino = circulacion.destino
            individuo.save()
            #Lo agregamos al registro
            circulacion.chofer = individuo
            circulacion.save()
            return redirect('permisos:ver_circulacion_temporal', token=circulacion.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Chofer", 'form': form, 'boton': "Cargar", })

def circ_cargar_acomp(request, token, individuo_id=None):
    individuo = None
    if individuo_id:
        individuo = Individuo.objects.get(pk=individuo_id)
    form = IngresanteForm(instance=individuo)
    if request.method == "POST":
        #obtenemos ingreso
        form = IngresanteForm(request.POST, instance=individuo)
        if form.is_valid():
            circulacion = CirculacionTemporal.objects.get(token=token)
            #actualizamos individuo con los datos nuevos
            individuo = actualizar_individuo(form)
            #individuo.origen = circulacion.origen
            individuo.destino = circulacion.destino
            individuo.save()
            #Lo agregamos al registro
            circulacion.acompañante = individuo
            circulacion.save()
            return redirect('permisos:ver_circulacion_temporal', token=circulacion.token)
    return render(request, "extras/generic_form.html", {'titulo': "Cargar Acompañante", 'form': form, 'boton': "Cargar", })

def finalizar_circulacion(request, token):
    circulacion = CirculacionTemporal.objects.get(token=token)
    # Dar atributos de Circulacion Temporal a chofer y acompañante
    atributo = Atributo(individuo=circulacion.chofer)
    atributo.tipo = 'CT'
    atributo.aclaracion = "Obtenido por Circulacion id: " + str(circulacion.pk)
    atributo.save()
    if circulacion.acompañante:
        atributo = Atributo(individuo=circulacion.acompañante)
        atributo.tipo = 'CT'
        atributo.aclaracion = "Obtenido por Circulacion id: " + str(circulacion.pk)
        atributo.save()
    # Generar PDF con permiso de circulacion
    circulacion.generar_pdf()
    # Enviar Mail de Aprobacion
    if SEND_MAIL:
        to_email = circulacion.email_contacto
        #Preparamos el correo electronico
        mail_subject = 'COE2020 Permiso de Circulacion Temporal Otorgado'
        message = render_to_string('emails/circulacion_generada.html', {
            'circulacion': circulacion,
        })
        #Instanciamos el objeto mail con destinatario
        email = EmailMessage(mail_subject, message, to=[to_email])
        email.send()
    # Evolucionar circulacion > Aprobada
    circulacion.estado = 'A'
    #Guardamos cambios
    circulacion.save()
    #volvemos a mostrar el panel
    return redirect('permisos:ver_circulacion_temporal', token=circulacion.token)

def ver_comprobante_circulacion(request, token):
    circulacion = CirculacionTemporal.objects.get(token=token)
    circulacion.generar_pdf()
    return HttpResponseRedirect('/archivos/circulacion/'+circulacion.token+'.pdf')

#Administrar
@permission_required('operadores.permisos')
def menu_permisos(request):
    return render(request, 'menu_permisos.html', {})

@superuser_required
def situacion_restricciones(request):
    niveles = NivelRestriccion.objects.all()
    try:
        grosor = int(math.ceil(12 / niveles.count()))
        return render(request, 'niveles_restriccion.html', {
            'niveles': niveles,
            'grosor': grosor,
        })
    except:
        return redirect('permisos:crear_nivelrestriccion')

@superuser_required
def crear_nivelrestriccion(request, nivel_id=None):
    nivel = None
    if nivel_id:
        nivel = NivelRestriccion.objects.get(pk=nivel_id)
    form = NivelRestriccionForm(instance=nivel)
    if request.method == "POST":
        form = NivelRestriccionForm(request.POST, instance=nivel)
        if form.is_valid():
            form.save()
            return redirect('permisos:situacion_restricciones')
    return render(request, "extras/generic_form.html", {'titulo': "Modificar nivel de Restriccion", 'form': form, 'boton': "Modificar", })

@superuser_required
def activar_nivel(request, nivel_id):
    nivel = NivelRestriccion.objects.get(pk=nivel_id)
    if request.method == "POST":
        nivel.activa = True
        nivel.save()
        return redirect('permisos:situacion_restricciones')
    return render(request, "extras/confirmar.html", {
            'titulo': "Activar Nivel "+nivel.get_color_display(),
            'message': "Esto Modificara todos los permisos Digitales Entregados.",
            'has_form': True,
        }
    )

#Permisos
@permission_required('operadores.permisos')
def lista_activos(request):
    permisos = Permiso.objects.filter(endda__gt=timezone.now())
    return render(request, 'lista_permisos.html', {
        'titulo': "Permisos Activos",
        'permisos': permisos,
        'has_table': True,
    })

@permission_required('operadores.permisos')
def lista_vencidos(request):
    permisos = Permiso.objects.filter(endda__lt=timezone.now())
    return render(request, 'lista_permisos.html', {
        'titulo': "Permisos Vencidos",
        'permisos': permisos,
        'has_table': True,
    })

@permission_required('operadores.permisos')
def ver_permiso(request, permiso_id, individuo_id):
    permiso = Permiso.objects.select_related('individuo')
    permiso = permiso.get(pk=permiso_id)
    if individuo_id == permiso.individuo.id:
        return render(request, 'ver_permiso.html', {
            'individuo': permiso.individuo,
            'permiso': permiso,
        })
    else:
        return render(request, 'extras/error.html', {
            'titulo': 'Permiso Inexistente',
            'error': "El permiso al que intenta acceder no existe.",
        })

@permission_required('operadores.permisos')
def eliminar_permiso(request, permiso_id):
    permiso = Permiso.objects.get(pk=permiso_id)
    permiso.begda = timezone.now() - timedelta(days=7)#Lo mandamos una semana para atras
    permiso.endda = timezone.now() - timedelta(days=7)#Lo mandamos una semana para atras
    permiso.operador = obtener_operador(request)
    permiso.aclaracion = permiso.aclaracion + ' | Dado de baja por: ' + str(permiso.operador)
    permiso.save()
    return redirect('permisos:lista_activos')

#Ingresos Provinciales
@permission_required('operadores.permisos')
def situacion_ingresos(request):
    ingresos = IngresoProvincia.objects.all()
    ingresos = ingresos.prefetch_related('individuos')
    #Obtenemos los totales
    totales_tipo = [(tipo[0], tipo[1], ingresos.filter(tipo=tipo[0]).count()) for tipo in TIPO_INGRESO]
    totales_estado = [(estado[0], estado[1], ingresos.filter(estado=estado[0]).count()) for estado in ESTADO_INGRESO]
    #Preparamos la lista de ingresos de hoy
    ingresos_hoy = ingresos.filter(estado='A')
    ingresos_hoy = ingresos_hoy.filter(fecha_llegada__date=timezone.now().date())
    #GRAFICACION
    #Fechas del Grafico
    dias = [timezone.now() + timedelta(days=x) for x in range(0,7)]
    dias = [dia.date() for dia in dias]
    #Generamos Grafico de Ingresos:
    graf_ingresos = obtener_grafico('graf_ingresos', 'Grafico Ingresos Provinciales', 'L')
    graf_ingresos.reiniciar_datos()
    #Optimizamos cantidades
    cantidades = {}
    for ingreso in ingresos.filter(estado='A', fecha_llegada__date__gte=timezone.now().date()):
        if date2str(ingreso.fecha_llegada.date())+'@'+ingreso.tipo[0] in cantidades:
            cantidades[(date2str(ingreso.fecha_llegada.date())+'@'+ingreso.tipo[0])] += 1
        else:
            cantidades[(date2str(ingreso.fecha_llegada.date())+'@'+ingreso.tipo[0])] = 1
    #Generamos grafico
    for dia in dias:
        for tipo in TIPO_INGRESO:
            try:
                cant = cantidades[date2str(dia)+'@'+tipo[0]]
            except:
                cant = 0
            graf_ingresos.bulk_dato(dia, tipo[1], date2str(dia), cant)
    graf_ingresos.bulk_save()
    return render(request, 'situacion_ingresos.html', {
            'totales_tipo': totales_tipo,
            'totales_estado': totales_estado,
            'ingresos_hoy': ingresos_hoy,
            'graf_ingresos': graf_ingresos,
        }
    )

@permission_required('operadores.permisos')
def lista_ingresos(request, estado=None, tipo=None):
    ingresos = IngresoProvincia.objects.all()
    #Filtramos de ser necesario
    if not estado and not tipo:
        ingresos = ingresos.exclude(estado='B')
    if estado:
        ingresos = ingresos.filter(estado=estado)
    #Optimizamos
    ingresos = ingresos.select_related('origen', 'destino', 'operador')
    ingresos = ingresos.prefetch_related('individuos')
    #Lanzamos listado
    return render(request, 'lista_ingresos.html', {
        'titulo': "Ingresos Pedidos",
        'ingresos': ingresos,
        'has_table': True,
    })

@permission_required('operadores.permisos')
def ingreso_enviar_email(request, ingreso_id):
    ingreso = IngresoProvincia.objects.get(pk=ingreso_id)
    form = EmailForm(initial={'destinatario': ingreso.email_contacto})
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            if SEND_MAIL:
                to_email = form.cleaned_data['destinatario']
                #Preparamos el correo electronico
                mail_subject = form.cleaned_data['asunto']
                message = render_to_string('emails/ingreso_contacto.html', {
                        'ingreso': ingreso,
                        'cuerpo': form.cleaned_data['cuerpo'],
                    })
                #Guardamos el mail
                Emails_Ingreso(ingreso=ingreso, asunto=mail_subject, cuerpo=form.cleaned_data['cuerpo'], operador=obtener_operador(request)).save()
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
        return redirect('permisos:ver_ingreso_provincial', token=ingreso.token)
    return render(request, "extras/generic_form.html", {'titulo': "Enviar Correo Electronico", 'form': form, 'boton': "Enviar", })

@permission_required('operadores.permisos')
def aprobar_ingreso(request, ingreso_id):
    ingreso = IngresoProvincia.objects.get(pk=ingreso_id)
    form = AprobarForm(initial={
        'fecha': ingreso.fecha_llegada,
    })
    if request.method == 'POST':
        form = AprobarForm(request.POST)
        if form.is_valid():
            if SEND_MAIL:
                to_email = ingreso.email_contacto
                #Preparamos el correo electronico
                mail_subject = 'COE2020 Aprobamos tu Ingreso a la Provincia Jujuy!'
                message = render_to_string('emails/ingreso_aprobado.html', {
                        'ingreso': ingreso,
                    })
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
            #Aprobamos el Ingreso
            ingreso.estado = 'A'
            ingreso.fecha_llegada = form.cleaned_data['fecha']
            ingreso.operador = obtener_operador(request)
            ingreso.generar_pdf()
            ingreso.save()
            return redirect('permisos:ver_ingreso_provincial', token=ingreso.token)
    return render(request, "extras/generic_form.html", {'titulo': "Aprobar Ingreso Provincial", 'form': form, 'boton': "Aprobar", })

@permission_required('operadores.permisos')
def eliminar_ingreso(request, ingreso_id):
    ingreso = IngresoProvincia.objects.get(pk=ingreso_id)
    ingreso.estado = 'B'
    ingreso.operador = obtener_operador(request)
    ingreso.save()
    return redirect('permisos:lista_ingresos')

#Circulacion Temporal
@permission_required('operadores.permisos')
def lista_circulaciones(request, estado=None, tipo=None):
    circulaciones = CirculacionTemporal.objects.all()
    #Filtramos de ser necesario
    if not estado and not tipo:
        circulaciones = circulaciones.exclude(estado='B')
    if estado:
        circulaciones = circulaciones.filter(estado=estado)
    if tipo:
        circulaciones = circulaciones.filter(tipo=tipo)
    #Optimizamos
    circulaciones = circulaciones.select_related('origen', 'destino')
    circulaciones = circulaciones.prefetch_related('chofer')
    #Lanzamos listado
    return render(request, 'lista_circulaciones.html', {
        'titulo': "Permisos de Circulacion Temporales",
        'circulaciones': circulaciones,
        'has_table': True,
    })

@permission_required('operadores.permisos')
def eliminar_circulacion(request, circulacion_id):
    circulacion = CirculacionTemporal.objects.get(pk=circulacion_id)
    circulacion.estado = 'B'
    circulacion.save()
    return redirect('permisos:lista_circulaciones')

@permission_required('operadores.permisos')
def reactivar_circulacion(request, circulacion_id):
    circulacion = CirculacionTemporal.objects.get(pk=circulacion_id)
    circulacion.estado = 'C'
    circulacion.save()
    return redirect('permisos:ver_circulacion_temporal', token=circulacion.token)

@permission_required('operadores.permisos')
def circulacion_enviar_email(request, circulacion_id):
    circulacion = CirculacionTemporal.objects.get(pk=circulacion_id)
    form = EmailForm(initial={'destinatario': circulacion.email_contacto})
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            if SEND_MAIL:
                to_email = form.cleaned_data['destinatario']
                #Preparamos el correo electronico
                mail_subject = form.cleaned_data['asunto']
                message = render_to_string('emails/circulacion_contacto.html', {
                        'circulacion': circulacion,
                        'cuerpo': form.cleaned_data['cuerpo'],
                    })
                #Guardamos el mail
                Emails_Circulacion(circulacion=circulacion, asunto=mail_subject, cuerpo=form.cleaned_data['cuerpo'], operador=obtener_operador(request)).save()
                #Instanciamos el objeto mail con destinatario
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
        return redirect('permisos:ver_circulacion_temporal', token=circulacion.token)
    return render(request, "extras/generic_form.html", {'titulo': "Enviar Correo Electronico", 'form': form, 'boton': "Enviar", })