#Imports de python
import copy
import json
import logging
import traceback
from base64 import b64decode

#Imports de Django
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
#Imports Extras
from fcm_django.models import FCMDevice
#Imports del proyecto
from coe.constantes import LAST_DATETIME
from operadores.models import Operador
from georef.models import Nacionalidad, Localidad
#Imports de la app
from .choices import TIPO_PERMISO
from .models import Individuo, AppData, Domicilio, GeoPosicion
from .models import Atributo, Sintoma, Situacion, Seguimiento
from .models import Permiso
from .tokens import TokenGenerator
from .geofence import controlar_distancia, buscar_permiso, validar_permiso

#Definimos logger
logger = logging.getLogger("apis")

@csrf_exempt
@require_http_methods(["GET"])
def AppConfig(request):
    return JsonResponse(
        {
            "action":"AppConfig",
            #WebServices
            "WebServices":
            {
                "tipo_permisos": reverse("ws_urls:tipo_permiso"),
                "localidad": reverse("georef:localidad-autocomplete"),
                "barrio": reverse("georef:barrio-autocomplete"),
                "logs": "/archivos/logs/apis.txt",
            },
            #Registro:
            "Registro":
            {
                "url": reverse("app_urls:registro"),
                "fields_request": 
                {
                    "dni_individuo": "str",
                    "apellido": "str",
                    "nombre": "str",
                    "localidad": "int: id_localidad",
                    "localidad_nombre": "str: nombre completo desde ws",
                    "barrio": "int: id_barrio (opcional)",
                    "direccion_calle": "str",
                    "direccion_numero": "str",
                    "telefono": "str",
                    "email": "str (Opcional)",
                    "push_notification_id": "str",
                },
                "fields_response": 
                {
                    "action": "registro",
                    "realizado": "bool",
                    "token": "str: para validar envios posteriores",
                    "error": "str (Solo si hay errores)",
                },
            },
            "FotoPerfil":
            {
                "url": reverse("app_urls:foto_perfil"),
                "fields_request": 
                {
                    "dni_individuo": "str",
                    "token": "str: Obtenido en respuesta registro",
                    "imagen": "Base64",

                },
                "fields_response": 
                {
                    "action": "registro_avanzado",
                    "realizado": "bool",
                    "error": "str (Solo si hay errores)",
                }
            },
            #Encuesta
            "Encuesta":
            {
                "url": reverse("app_urls:encuesta"),
                "fields_request": 
                {
                    "dni_individuo": "str",
                    "token": "str: Obtenido en respuesta registro",
                    "pais_riesgo": "bool",
                    "contacto_extranjero": "bool",
                    "fiebre": "bool",
                    "tos": "bool",
                    "dif_respirar": "bool",
                    "riesgo": "int (1:Alto,2:Medio,3:Bajo)",
                    "latitud": "float", 
                    "longitud": "float",
                },
                "fields_response": 
                {
                    "action": "encuesta",
                    "realizado": "bool",
                    "error": "str (Solo si hay errores)",
                }
            },
            #Start Tracking
            "StartTracking":
            {
                "url": reverse("app_urls:start_tracking"),
                "fields": 
                {
                    "dni_individuo": "str",
                    "token": "str: Obtenido en respuesta registro",
                    "dni_operador": "str",
                    "password": "str",
                    "latitud": "float", 
                    "longitud": "float",
                },
                "fields_response": 
                {
                    "action": "start_tracking",
                    "realizado": "bool",
                    "error": "str (Solo si hay errores)",
                }
            },
            #Tracking
            "tracking": 
            {
                "url": reverse("app_urls:tracking"),
                "fields": 
                {
                    "dni_individuo": "str",
                    "token": "str: Obtenido en respuesta registro",
                    "fecha": "str: YYYYMMDD",
                    "hora": "str: HHMM",
                    "latitud": "float", 
                    "longitud": "float",
                },
                "fields_response": 
                {
                    "action": "tracking",
                    "realizado": "bool",
                    "alerta": "bool",
                    "notif_titulo": "str (Titulo notificacion Local)",
                    "notif_mensaje": "str (Mensaje notificacion Local)",
                    "distancia" : "float (en metros)",
                    "prox_tracking": "int (Minutos hasta proximo envio)",
                    "error": "str (Solo si hay errores)",
                },
                "parametros":
                {
                    'alerta_distancia': 50,
                    'alerta_mensaje': 'Alerta, usted se ha alejado por mas de 50 metros del punto fijado.',
                    'critico_distancia': 100,
                    'critico_mensaje': 'Usted se ha alejado mas de 100 metros del punto fijado, las fuerzas de seguridad estan siendo informadas.',
                },
            },
            #Obtener Salvoconducto Digital
            "get_salvoconducto":
            {
                "url": reverse("app_urls:get_salvoconducto"),
                "fields":
                {
                    "dni_individuo": "str",
                    "token": "str: Obtenido en respuesta registro",            
                },
                "fields_response": 
                {
                    "action": "salvoconducto",
                    "realizado": "bool",
                    "tipo_permiso": "str: Descripcion del permiso",
                    "fecha_inicio": "datefield",
                    "hora_inicio": "timefield",
                    "fecha_fin": "datefield",
                    "hora_fin": "str: timefield",
                    "imagen": "url",
                    "qr": "url",
                    "texto": "str: leyenda de permiso autorizado",
                    "error": "str (Solo si hay errores/rechaza pedido)",
                },
            },
            #Salvoconducto Digital
            "salvoconducto":
            {
                "url": reverse("app_urls:salvoconducto"),
                "fields":
                {
                    "dni_individuo": "str",
                    "token": "str: Obtenido en respuesta registro",
                    "tipo_permiso": "str(1):id de TIPO_PERMISO",
                    "fecha_ideal": "str: YYYYMMDD",
                    "hora_ideal": "str: HHMM",
                },
                "fields_response": 
                {
                    "action": "salvoconducto",
                    "realizado": "bool",
                    "tipo_permiso": "str: Descripcion del permiso",
                    "fecha_inicio": "datefield",
                    "hora_inicio": "timefield",
                    "fecha_fin": "datefield",
                    "hora_fin": "str: timefield",
                    "imagen": "url",
                    "qr": "url",
                    "texto": "str: leyenda de permiso autorizado",
                    "error": "str (Solo si hay errores/rechaza pedido)",
                },
                "parametros":
                {
                    'TIPO_PERMISO': {tp[0]:tp[1] for tp in TIPO_PERMISO if tp[0] != 'P'},
                },
            },
            #Control de SalvoConducto
            "control_salvoconducto":
            {
                "url": reverse("app_urls:control_salvoconducto"),
                "fields":
                {
                    "dni_operador": "str (Del Dueño del celular)",
                    "qr_code": "El QR que se leyo",
                    "latitud": "float", 
                    "longitud": "float",
                },
                "fields_response": 
                {
                    "action": "salvoconducto",
                    "realizado": "bool",
                    "tipo_permiso": "str: Descripcion del permiso",
                    "fecha_inicio": "datefield",
                    "hora_inicio": "timefield",
                    "fecha_fin": "datefield",
                    "hora_fin": "str: timefield",
                    "imagen": "url",
                    "qr": "url",
                    "texto": "str: leyenda de permiso autorizado",
                    "error": "str (Solo si hay errores/rechaza pedido)",
                },
            },
            #Notifaciones
            "Notificaciones":
            {
                "url": reverse("app_urls:notificacion"),
                "fields":
                {
                    "dni_individuo": "str",
                    "token": "str: Obtenido en respuesta registro",
                },
            "fields_response": 
                {
                    "action": "notificacion",
                    "realizado": "bool",
                    "notif_titulo": "str (Titulo notificacion Local | si realizado=True)",
                    "notif_mensaje": "str (Mensaje notificacion Local | si realizado=True)",
                    "error": "str (Solo si hay errores)",
                },
            },
        },
        safe=False,
    )

@csrf_exempt
@require_http_methods(["POST"])
def registro(request):
    try:
        data = None
        #Registramos ingreso de info
        #Recibimos el json
        data = json.loads(request.body.decode("utf-8"))
        logger.info("\nregistro:"+str(timezone.now())+"|"+str(data))
        #Obtenemos datos basicos:
        nac = Nacionalidad.objects.filter(nombre__icontains="Argentina").first()
        #Agarramos el dni
        if "dni" in data:
            num_doc = str(data["dni"]).upper()
        else:
            num_doc = str(data["dni_individuo"]).upper()
        #Buscamos al individuo en la db
        try:#Si lo encontramos, lo usamos
            individuo = Individuo.objects.get(num_doc=num_doc)
        #Si no existe lo creamos
        except Individuo.DoesNotExist:
            individuo = Individuo()
            individuo.individuo = individuo
            individuo.num_doc = num_doc
            individuo.apellidos = data["apellido"]
            individuo.nombres = data["nombre"]
            individuo.nacionalidad = nac
            individuo.observaciones = "AUTODIAGNOSTICO"
            individuo.save()
        #PROCESAMOS INFO DE APP
        if not hasattr(individuo,"appdata"):
            appdata = AppData()
            appdata.individuo = individuo
        else:
            appdata = individuo.appdata
        #Procesamos telefono si lo envio
        if not individuo.telefono == "+549388":
            individuo.telefono = str(data["telefono"])
            individuo.save()
        else:
            appdata.telefono = str(data["telefono"])
        #Procesamos email si lo envio
        if "email" in data:
            if not individuo.email:
                individuo.email = data["email"]
            else:
                appdata.email = data["email"]
        #Registramos push_not_id
        if "push_notification_id" in data:
            device = FCMDevice()
            device.name = individuo.num_doc
            device.registration_id = data["push_notification_id"]
            device.type = 'android'
            if "device_id" in data:
                device.device_id = data["device_id"]
            device.save()
            #Le registramos su dispositivo
            individuo.device = device
            individuo.save()
        #Guardamos
        appdata.fecha = timezone.now()
        appdata.save()
        #Cargamos un nuevo domicilio:
        Domicilio.objects.filter(individuo=individuo, aclaracion="AUTODIAGNOSTICO").delete()
        domicilio = Domicilio(individuo=individuo)
        domicilio.calle = data["direccion_calle"]
        domicilio.numero = str(data["direccion_numero"])
        if "localidad" in data:
            domicilio.localidad = Localidad.objects.get(pk=data["localidad"])
        elif "localidad_nombre" in data:
            localidad, departamento = data["localidad_nombre"].split('(')
            localidad = localidad[:-1]
            departamento = departamento[:-1]
            domicilio.localidad = Localidad.objects.get(nombre=localidad, departamento__nombre=departamento)
        else:
            domicilio.localidad = Localidad.objects.first()
        domicilio.aclaracion = "AUTODIAGNOSTICO"
        domicilio.save()
        #Respondemos que fue procesado
        logger.info("Exito!")
        return JsonResponse(
            {
                "action":"registro",
                "realizado": True,
                "token": TokenGenerator(individuo),
            },
            safe=False
        )
    except Exception as e:
        logger.info("Falla: "+str(e))
        return JsonResponse(
            {
                "action":"registro",
                "realizado": False,
                "error": str(e),
                "error_contexto": str(e.__context__),
                "error_traceback": str(traceback.format_exc()),
            },
            safe=False,
            status=400,
        )

@csrf_exempt
@require_http_methods(["POST"])
def foto_perfil(request):
    try:
        data = None
        #Registramos ingreso de info
        #Recibimos el json
        data = json.loads(request.body.decode("utf-8"))
        data2 = copy.copy(data)
        data2["imagen"] = data2["imagen"][:25]+'| full |'+data2["imagen"][-25:]
        logger.info("\nfoto_perfil:"+str(timezone.now())+"|"+str(data2))
        #Agarramos el dni
        if "dni" in data:
            num_doc = str(data["dni"]).upper()
        else:
            num_doc = str(data["dni_individuo"]).upper()
        #Buscamos al individuo en la db
        individuo = Individuo.objects.get(num_doc=num_doc)
        #ACA CHEQUEAMOS TOKEN

        #Cargamos la foto:
        image_data = b64decode(data['imagen'])
        individuo.fotografia = ContentFile(image_data, individuo.num_doc+'.jpg')
        individuo.save()
        #Terminamos proceso
        logger.info("Exito!")
        return JsonResponse(
            {
                "action":"foto_perfil",
                "realizado": True,
            },
            safe=False
        )
    except Exception as e:
        logger.info("Falla: "+str(e))
        return JsonResponse(
            {
                "action":"foto_perfil",
                "realizado": False,
                "error": str(e),
                "error_contexto": str(e.__context__),
                "error_traceback": str(traceback.format_exc()),
            },
            safe=False,
            status=400,
        )

@csrf_exempt
@require_http_methods(["POST"])
def encuesta(request):
    try:
        data = None
        #Registramos ingreso de info
        #Recibimos el json
        data = json.loads(request.body.decode("utf-8"))
        logger.info("\nencuesta:"+str(timezone.now())+"|"+str(data))
        #Agarramos el dni
        if "dni" in data:
            num_doc = str(data["dni"]).upper()
        else:
            num_doc = str(data["dni_individuo"]).upper()
        #Buscamos al individuo en la db
        individuo = Individuo.objects.get(num_doc=num_doc)
        #ACA CHEQUEAMOS TOKEN

        #Cargamos datos importantes:
        #Atributos
        Atributo.objects.filter(individuo=individuo, aclaracion="ENCUESTAAPP").delete()
        if data["pais_riesgo"] or data["contacto_extranjero"]:
            atributo = Atributo(individuo=individuo)
            atributo.tipo = "CE"
            atributo.aclaracion = "ENCUESTAAPP"
            atributo.save()
        #Sintomas
        Sintoma.objects.filter(individuo=individuo, aclaracion="ENCUESTAAPP").delete()
        if data["fiebre"]:
            sintoma = Sintoma(individuo=individuo, tipo="FIE", aclaracion="ENCUESTAAPP")
            sintoma.save()
        if data["tos"]:
            sintoma = Sintoma(individuo=individuo, tipo="TOS", aclaracion="ENCUESTAAPP")
            sintoma.save()
        if data["dif_respirar"]:
            sintoma = Sintoma(individuo=individuo, tipo="DPR", aclaracion="ENCUESTAAPP")
            sintoma.save()
        #Resultado
        individuo.appdata.estado = [0,"R","A","V"][data["riesgo"]]
        individuo.appdata.save()
        #Cargamos nueva situacion
        if data["riesgo"] > 1:
            Situacion.objects.filter(individuo=individuo, aclaracion="AUTODIAGNOSTICO").delete()
            situacion = Situacion()
            situacion.individuo = individuo
            situacion.estado = 40
            situacion.conducta = "C"
            situacion.aclaracion = "AUTODIAGNOSTICO"
            situacion.save()
        #Geoposicion
        if data["latitud"] and data["longitud"]:
            geopos = GeoPosicion()
            geopos.individuo = individuo
            geopos.tipo = 'AD'
            geopos.latitud = data["latitud"]
            geopos.longitud = data["longitud"]
            geopos.aclaracion = "AUTODIAGNOSTICO"
            geopos.save()
        logger.info("Exito!")
        return JsonResponse(
            {
                "action":"encuesta",
                "realizado": True,
            },
            safe=False
        )
    except Exception as e:
        logger.info("Falla: "+str(e))
        return JsonResponse(
            {
                "action":"encuesta",
                "realizado": False,
                "error": str(e),
                "error_contexto": str(e.__context__),
                "error_traceback": str(traceback.format_exc()),
            },
            safe=False,
            status=400,
        )

@csrf_exempt
@require_http_methods(["POST"])
def start_tracking(request):
    try:
        data = None
        #Recibimos el json
        data = json.loads(request.body.decode("utf-8"))
        data2 = copy.copy(data)
        data2["password"] = "OCULTA"
        logger.info("\nstart_tracking:"+str(timezone.now())+"|"+str(data2))
        #Agarramos el dni
        if "dni" in data:
            num_doc = str(data["dni"]).upper()
        else:
            num_doc = str(data["dni_individuo"]).upper()
        #Buscamos al individuo en la db
        individuo = Individuo.objects.get(num_doc=num_doc)
        #ACA CHEQUEAMOS TOKEN

        #Chequeamos credenciales de operador
        operador = Operador.objects.get(num_doc=data["dni_operador"])
        user = authenticate(username=operador.usuario, password=data["password"])
        if not user:
            return JsonResponse(
            {
                "action":"start_tracking",
                "realizado": False,
                "error": "El operador no existe.",
            },
            safe=False,
            status=400,
        )
        #Guardamos la geoposicion BASE (Eliminamos todas las anteriores)
        GeoPosicion.objects.filter(individuo=individuo, tipo__in=('ST', 'TC')).delete()
        geopos = GeoPosicion()
        geopos.individuo = individuo
        geopos.tipo = 'ST'
        geopos.latitud = data["latitud"]
        geopos.longitud = data["longitud"]
        geopos.aclaracion = "INICIO TRACKING"
        geopos.save()
        #Cargamos Inicio de Seguimiento:
        Seguimiento.objects.filter(tipo__in=("IT","AT", "FT")).delete()
        seguimiento = Seguimiento()
        seguimiento.individuo = individuo
        seguimiento.tipo = "IT"
        seguimiento.aclaracion = "INICIO TRACKING: " + str(geopos.latitud)+", "+str(geopos.longitud)
        seguimiento.save()
        #Respondemos
        logger.info("Exito!")
        return JsonResponse(
            {
                "action":"start_tracking",
                "realizado": True,
            },
            safe=False
        )
    except Exception as e:
        logger.info("Falla: "+str(e))
        return JsonResponse(
            {
                "action":"start_tracking",
                "realizado": False,
                "error": str(e),
                "error_contexto": str(e.__context__),
                "error_traceback": str(traceback.format_exc()),
            },
            safe=False,
            status=400,
        )

@csrf_exempt
@require_http_methods(["POST"])
def tracking(request):
    try:
        data = None
        #Recibimos el json
        data = json.loads(request.body.decode("utf-8"))
        logger.info("\ntracking:"+str(timezone.now())+"|"+str(data))
        #Agarramos el dni
        if "dni" in data:
            num_doc = str(data["dni"]).upper()
        else:
            num_doc = str(data["dni_individuo"]).upper()
        #Buscamos al individuo en la db
        individuo = Individuo.objects.get(num_doc=num_doc)
        #ACA CHEQUEAMOS TOKEN

        #Guardamos nueva posgps
        geopos = GeoPosicion()
        geopos.individuo = individuo
        geopos.tipo = 'RG'
        geopos.latitud = data["latitud"]
        geopos.longitud = data["longitud"]
        geopos.aclaracion = "TRACKING"
        geopos.fecha = timezone.datetime(
            int(data["fecha"][0:4]),
            int(data["fecha"][4:6]),
            int(data["fecha"][6:8]),
            int(data["hora"][0:2]),
            int(data["hora"][2:4]),
        )
        #Chequeamos distancia:
        geopos.distancia = controlar_distancia(geopos)
        #Si es mayor a alerta la marcamos
        notif_titulo = None
        notif_mensaje = None
        if geopos.distancia > 50:
            geopos.alerta = True
            notif_titulo = "Covid19 - Alerta por Distancia"
            notif_mensaje = "Usted se ha alejado a "+str(int(geopos.distancia))+"mts del area permitida."
        #Guardamos solo si vale la pena
        if geopos.distancia > 5:
            geopos.save()
        #Realizamos controles avanzados
        
        #Controlamos posicion:
        logger.info("Exito")
        return JsonResponse(
            {
                "action":"tracking",
                "realizado": True,
                "prox_tracking": 5,#Minutos
                "distancia": int(geopos.distancia),
                "alerta": geopos.alerta,
                "notif_titulo": notif_titulo,
                "notif_mensaje": notif_mensaje,
            },
            safe=False
        )
    except Exception as e:
        logger.info("Falla: "+str(e))
        return JsonResponse(
            {
                "action":"tracking",
                "realizado": False,
                "error": str(e),
                "error_contexto": str(e.__context__),
                "error_traceback": str(traceback.format_exc()),
            },
            safe=False,
            status=400,
        )


@csrf_exempt
@require_http_methods(["POST"])
def salvoconducto(request):
    try:
        data = None
        #Recibimos el json
        data = json.loads(request.body.decode("utf-8"))
        logger.info("\nsalvoconducto:"+str(timezone.now())+"|"+str(data))
        #Agarramos el dni
        if "dni" in data:
            num_doc = str(data["dni"]).upper()
        else:
            num_doc = str(data["dni_individuo"]).upper()
        #Buscamos al individuo en la db
        individuo = Individuo.objects.select_related('appdata', 'domicilio_actual', 'situacion_actual')
        individuo = Individuo.objects.prefetch_related('permisos')
        individuo = individuo.get(num_doc=num_doc)
        #ACA CHEQUEAMOS TOKEN
        
        #Trabajamos
        #Chequear si no es policia, salud, funcionario >Permiso ilimitado.
            #RESPONDER CON FULL GREEN
        #Obtenemos datos del pedido de permiso:
        permiso = data["tipo_permiso"]
        fecha = timezone.datetime(
            int(data["fecha_ideal"][0:4]),
            int(data["fecha_ideal"][4:6]),
            int(data["fecha_ideal"][6:8]),
            int(data["hora_ideal"][0:2]),
            int(data["hora_ideal"][2:4]),
        )
        #Validamos si es factible:
        permiso = validar_permiso(individuo, data)
        #Si fue aprobado, Creamos Permiso
        if permiso.aprobar:
            permiso.individuo = individuo
            permiso.tipo = data["tipo_permiso"]
            permiso.localidad = individuo.domicilio_actual.localidad
            permiso.begda = timezone.now() + timedelta(days=1)
            permiso.endda = timezone.now() + timedelta(days=1, hours=2)
            permiso.aclaracion = "Requerido Via App."
            permiso.save()
            #Si todo salio bien
            logger.info("Exito")
            return JsonResponse(
                {
                    "action": "salvoconducto",
                    "realizado": permiso.aprobar,
                    "tipo_permiso": permiso.get_tipo_display(),
                    "fecha_inicio": permiso.begda.date(),
                    "hora_inicio": permiso.begda.time(),
                    "fecha_fin": permiso.endda.date(),
                    "hora_fin": permiso.endda.time(),
                    "imagen": individuo.get_foto(),
                    "qr": individuo.get_qr(),
                    "texto": permiso.aclaracion,
                },
                safe=False
            )
        else:
            #Si todo salio bien
            logger.info("Denegado: " + permiso.aclaracion)
            return JsonResponse(
                {
                    "action": "salvoconducto",
                    "realizado": permiso.aprobar,
                    "error": permiso.aclaracion,
                },
                safe=False
            )
    except Exception as e:
        logger.info("Falla: "+str(e))
        return JsonResponse(
            {
                "action":"salvoconducto",
                "realizado": False,
                "error": str(e),
                "error_contexto": str(e.__context__),
                "error_traceback": str(traceback.format_exc()),
            },
            safe=False,
            status=400,
        )

@csrf_exempt
@require_http_methods(["POST"])
def get_salvoconducto(request):
    try:
        data = None
        #Recibimos el json
        data = json.loads(request.body.decode("utf-8"))
        logger.info("\nget_salvoconducto:"+str(timezone.now())+"|"+str(data))
        #Agarramos el dni
        if "dni" in data:
            num_doc = str(data["dni"]).upper()
        else:
            num_doc = str(data["dni_individuo"]).upper()
        #Buscamos al individuo en la db
        individuo = Individuo.objects.select_related('appdata').get(num_doc=num_doc)
        #ACA CHEQUEAMOS TOKEN
        
        #Buscamos permiso
        permiso = buscar_permiso(individuo)
        #Damos respuesta
        logger.info("Exito")
        return JsonResponse(
            {
                "action": "get_salvoconducto",
                "realizado": True,
                "tipo_permiso": permiso.get_tipo_display(),
                "fecha_inicio": permiso.begda.date(),
                "hora_inicio": permiso.begda.time(),
                "fecha_fin": permiso.endda.date(),
                "hora_fin": permiso.endda.time(),
                "imagen": individuo.get_foto(),
                "qr": individuo.get_qr(),
                "texto": permiso.aclaracion,

            },
            safe=False
        )
    except Exception as e:
        logger.info("Falla: "+str(e))
        return JsonResponse(
            {
                "action":"get_salvoconducto",
                "realizado": False,
                "error": str(e),
                "error_contexto": str(e.__context__),
                "error_traceback": str(traceback.format_exc()),
            },
            safe=False,
            status=400,
        )

@csrf_exempt
@require_http_methods(["POST"])
def control_salvoconducto(request):
    try:
        data = None
        #Recibimos el json
        data = json.loads(request.body.decode("utf-8"))
        logger.info("\nget_salvoconducto:"+str(timezone.now())+"|"+str(data))
        #Agarramos el dni
        num_doc = str(data["dni_operador"]).upper()
        #Obtenemos el operador
        operador = Operador.objects.get(num_doc=num_doc)
        #Leemos QR y parceamos
        qr_code = data["qr_code"]
        if "@" in qr_code:#Es un DNI
            dni_qr = qr_code.split('@')[4]
            #Podriamos procesar el resto de la info del tipo
            #Fecha de Nacimiento
        elif "-" in qr_code:#Es permiso de App
            dni_qr = qr_code.split('-')[1]
        #Buscamos al individuo en la db
        individuo = Individuo.objects.select_related('appdata').get(num_doc=dni_qr)
        #ACA CHEQUEAMOS TOKEN
        
        #Guardamos registro de control
        geopos = GeoPosicion()
        geopos.individuo = individuo
        geopos.tipo = "CG"
        geopos.latitud = data["latitud"]
        geopos.longitud = data["longitud"]
        geopos.aclaracion = "Control de Salvoconducto"
        geopos.operador = operador
        geopos.save()
        #Buscamos permiso
        permiso = buscar_permiso(individuo, activo=True)
        #Damos respuesta
        logger.info("Exito")
        return JsonResponse(
            {
                "action": "get_salvoconducto",
                "realizado": True,
                "tipo_permiso": permiso.get_tipo_display(),
                "fecha_inicio": permiso.begda.date(),
                "hora_inicio": permiso.begda.time(),
                "fecha_fin": permiso.endda.date(),
                "hora_fin": permiso.endda.time(),
                "imagen": individuo.get_foto(),
                "qr": individuo.get_qr(),
                "texto": permiso.aclaracion,

            },
            safe=False
        )
    except Exception as e:
        logger.info("Falla: "+str(e))
        try:
            geopos.alerta = True
            geopos.save()
        except:
            pass
        return JsonResponse(
            {
                "action":"get_salvoconducto",
                "realizado": False,
                "error": str(e),
                "error_contexto": str(e.__context__),
                "error_traceback": str(traceback.format_exc()),
            },
            safe=False,
            status=400,
        )

@csrf_exempt
@require_http_methods(["POST"])
def notificacion(request):
    try:
        data = None
        #Recibimos el json
        data = json.loads(request.body.decode("utf-8"))
        logger.info("\nnotificacion:"+str(timezone.now())+"|"+str(data))
        #Agarramos el dni
        if "dni" in data:
            num_doc = str(data["dni"]).upper()
        else:
            num_doc = str(data["dni_individuo"]).upper()
        #Buscamos al individuo en la db
        individuo = Individuo.objects.select_related('appdata', 'appdata__notificacion').get(num_doc=num_doc)
        notificacion = individuo.appdata.notificacion
        #Damos respuesta
        logger.info("Exito")
        return JsonResponse(
            {
                "action": "notificacion",
                "realizado": True,
                "message":
                {
                    "title": notificacion.titulo,
                    "body": notificacion.mensaje,
                },
                "action": notificacion.get_accion_display(),

            },
            safe=False
        )
    except Exception as e:
        logger.info("Falla: "+str(e))
        return JsonResponse(
            {
                "action":"notificacion",
                "realizado": False,
                "error": str(e),
                "error_contexto": str(e.__context__),
                "error_traceback": str(traceback.format_exc()),
            },
            safe=False,
            status=400,
        )