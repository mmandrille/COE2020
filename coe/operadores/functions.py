#Imports django
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
#Imports de la app
from .models import Operador

#Definimos funciones del modulo
def obtener_operador(request):
    try:
        return Operador.objects.get(usuario=request.user)
    except Operador.DoesNotExist:
        return None

def obtener_permisos(usuario=None):
    if usuario and not usuario.is_superuser:
        return Permission.objects.filter(user=usuario)
    else:
        return Permission.objects.filter(
            content_type__app_label='operadores',
            content_type__model='operador').exclude(name__contains='Can ').order_by('name')

def generar_username(operador):
    nombre = operador.nombres.lower().replace(' ','')
    apellido = operador.apellidos.lower().replace(' ','')
    x = 0
    incorrecto = True
    while incorrecto:
        x += 1
        username = nombre[0:x] + apellido
        if User.objects.filter(username=username).exists():
            if x == len(nombre):
                return str(operador.num_doc)
        elif len(username) > 5:
            incorrecto = False
    return username

def crear_usuario(operador):
    usuario = User()
    usuario.username = generar_username(operador)
    usuario.is_active=False
    usuario.email = operador.email
    usuario.first_name = operador.nombres
    usuario.last_name = operador.apellidos
    usuario.is_staff = True
    usuario.save()
    return usuario

def obtener_localidad(operador):
    if operador.individuo:
        domicilio = operador.individuo.domicilio_actual
        if domicilio:
            return domicilio.localidad
    return None


def auditar_objeto(instancia):
    from django.contrib.contenttypes.models import ContentType
    from auditlog.models import LogEntry
    #Obtenemos datos basicos
    ct = ContentType.objects.get_for_model(instancia)
    #Buscamos registros
    registros = LogEntry.objects.filter(content_type=ct)
    registros = registros.filter(object_pk=instancia.pk)
    #Preparamos informe
    return registros