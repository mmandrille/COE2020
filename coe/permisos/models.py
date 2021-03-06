#Imports de python
import io
import qrcode
from datetime import timedelta
#Imports de django
from django.db import models
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.validators import RegexValidator
#Imports de paquetes extras
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from PyPDF2 import PdfFileWriter, PdfFileReader
from tinymce.models import HTMLField
from auditlog.registry import auditlog
from multiselectfield import MultiSelectField
#Imports del proyecto
from coe.settings import BASE_DIR, STATIC_ROOT, MEDIA_ROOT, LOADDATA
from georef.models import Provincia, Localidad
from informacion.models import Individuo
from operadores.models import Operador
from geotracking.models import GeoPosicion
#Imports de app
from .choices import COLOR_RESTRICCION, GRUPOS_PERMITIDOS
from .choices import TIPO_PERMISO, TIPO_ACTIVIDAD
from .choices import FRONTERA_CONTROL, TIPO_ALARMA
from .choices import COMBINACION_DNIxDIA
from .choices import TIPO_INGRESO, ESTADO_INGRESO
from .tokens import token_ingreso

# Create your models here.
class NivelRestriccion(models.Model):
    color = models.CharField('Nivel de Restriccion', choices=COLOR_RESTRICCION, max_length=1, default='B', unique=True)
    inicio_horario = models.SmallIntegerField("Hora de Inicio Actividades/f24")
    cierre_horario = models.SmallIntegerField("Hora de cierre Actividades/f24")
    poblacion_maxima = models.SmallIntegerField('Capacidad Adminitada en %')
    tramites_admitidos = MultiSelectField(choices=TIPO_PERMISO, null=True, blank=True)
    duracion_permiso = models.SmallIntegerField("Duracion de Permisos Digitales", default=1)
    grupos_diarios = MultiSelectField(choices=COMBINACION_DNIxDIA, null=True, blank=True)
    fecha_activacion = models.DateTimeField('Fecha de Activacion', null=True, blank=True)
    activa = models.BooleanField(default=False)

class Permiso(models.Model):
    individuo = models.ForeignKey(Individuo, on_delete=models.CASCADE, related_name="permisos")
    tipo = models.CharField('Tipo Permiso', choices=TIPO_PERMISO, max_length=1, default='C')
    localidad = models.ForeignKey(Localidad, on_delete=models.CASCADE, related_name="permisos")
    begda = models.DateTimeField('Inicio Permiso', default=timezone.now)
    endda = models.DateTimeField('Fin Permiso', default=timezone.now)
    controlador = models.BooleanField(default=False)
    aclaracion = HTMLField(null=True, blank=True)
    #Interno
    operador = models.ForeignKey(Operador, on_delete=models.SET_NULL, null=True, blank=True, related_name="permisos")
    #token = models.CharField('Token', max_length=35, default=generar_token, unique=True)
    #fecha = models.DateTimeField('Fecha de registro', default=timezone.now)
    def __str__(self):
        return self.get_tipo_display() + str(self.begda)[0:16]
    def estado(self):
        if self.endda > timezone.now():
            return "Activo"
        else:
            return "Vencido"

class IngresoProvincia(models.Model):
    tipo = models.CharField('Tipo Ingreso', choices=TIPO_INGRESO, max_length=1, default='P')
    email_contacto = models.EmailField('Correo Electronico de Contacto')
    fecha_llegada = models.DateTimeField('Fecha de Llegada', default=timezone.now)
    origen = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name="ingresos_provincial")
    destino = models.ForeignKey(Localidad, on_delete=models.CASCADE, related_name="ingresos_provincial")
    #Vehiculo
    marca = models.CharField('Marca del Vehiculo', max_length=200)
    modelo = models.CharField('Modelo del Vehiculo', max_length=200)
    patente = models.CharField('Identificacion Patente/Codigo', max_length=200)
    #Interno
    token = models.CharField('Token', max_length=50, default=token_ingreso, unique=True)
    fecha = models.DateTimeField('Fecha de registro', default=timezone.now)
    estado = models.CharField('Estado', choices=ESTADO_INGRESO, max_length=1, default='C')
    qrpath = models.CharField('qrpath', max_length=100, null=True, blank=True)
    operador = models.ForeignKey(Operador, on_delete=models.SET_NULL, null=True, blank=True, related_name="ingresos_provinciales")
    #Aclaraciones
    aclaracion = HTMLField(null=True)
    #Pasajeros
    individuos = models.ManyToManyField(Individuo, related_name='ingresante')
    #Archivos
    permiso_nacional = models.FileField('Permiso Nacional de Circulacion', upload_to='ingresos/', null=True, blank=True)
    dut = models.FileField('Permiso Nacional de Circulacion', upload_to='ingresos/', null=True, blank=True)
    plan_vuelo = models.FileField('Plan de Vuelo', upload_to='ingresos/', null=True, blank=True)
    def telefono(self):
        try:
            return self.individuos.all()[0].telefono
        except:
            return 'Sin informar'
    def get_qr(self):
        if self.qrpath:
            return self.qrpath
        else:
            path = MEDIA_ROOT + '/permisos/qrcode-'+str(self.id)+'.png'
            img = qrcode.make(self.token)#TIENE QUE SER URL A: redirect> 'permisos:ver_ingreso_aprobado' token=ingreso.token
            img.save(path)
            relative_path = 'archivos/permisos/qrcode-'+ str(self.id)+'.png'
            self.qrpath = relative_path
            self.save()
            return self.qrpath
    def generar_pdf(self):
        packet = io.BytesIO()
        # Se crear un nuevo pdf utilizando ReportLab        
        pdf = canvas.Canvas(packet, pagesize=A4)
        #escribimos textos del pdf
        #Fechamos
        pdf.setFont('Times-Roman', 9)
        pdf.drawString(475, 680, str(timezone.now())[0:16])
        #Armamos documento de permiso de ingreso a Jujuy
        pdf.setFont('Times-Roman', 18)
        pdf.drawString(20, 650, "PERMISO DE INGRESO A JUJUY")
        pdf.setFont('Times-Roman', 12)
        pdf.drawString(30, 630, self.get_tipo_display())
        pdf.drawString(30, 600, "Fecha de llegada: "+str(self.fecha_llegada)[0:16])
        pdf.drawString(30, 585, "Origen del Viaje: "+str(self.origen))
        pdf.drawString(30, 570, "Destino del Viaje: "+str(self.destino))
        pdf.drawString(30, 555, "Vehiculo: "+self.marca+" "+self.modelo+" "+self.patente)
        #Agregamos una linea
        pdf.line(200, 520, 400, 520)
        #Agregamos lista de pasajeros
        if self.individuos.exists():#Si existe
            pdf.drawString(30,530, "Pasajeros:")
            altura=500
            for individuo in self.individuos.all():
                pdf.drawString(30, altura, str(individuo))
                altura-= 20
        pdf.drawImage(self.get_qr(), 420, 520, 50*mm, 50*mm)
        pdf.save()
        #Se comienza el procedimiento para mergear pdfs
        packet.seek(0)
        nuevo_pdf = PdfFileReader(packet)
        # Leemos el pdf base
        existe_pdf = PdfFileReader(STATIC_ROOT+'/archivo/plantilla_nota.pdf', "rb")
        salida = PdfFileWriter()
        # Se agregan los datos de la persona que ser?? dada de alta, al pdf ya existente
        pagina = existe_pdf.getPage(0)
        pagina.mergePage(nuevo_pdf.getPage(0))
        salida.addPage(pagina)
        #Finalmente se escribe la salida, en un archivo real
        outputStream = open(MEDIA_ROOT+'/permisos/'+self.token+".pdf", "wb")
        salida.write(outputStream)
        outputStream.close()

class Emails_Ingreso(models.Model):
    ingreso = models.ForeignKey(IngresoProvincia, on_delete=models.CASCADE, related_name="emails")
    fecha = models.DateTimeField('Fecha de Envio', default=timezone.now)
    asunto = models.CharField('Asunto', max_length=100)
    cuerpo = models.CharField('Cuerpo', max_length=1000)
    operador = models.ForeignKey(Operador, on_delete=models.CASCADE, related_name="ingreso_emailsenviados")

class CirculacionTemporal(models.Model):#Transportes de Carga
    tipo = models.IntegerField('Actividad Excenta', choices=TIPO_ACTIVIDAD, default=1)
    email_contacto = models.EmailField('Correo Electronico de Contacto')
    chofer = models.ForeignKey(Individuo, on_delete=models.CASCADE, related_name="transportista", null=True, blank=True)
    acompa??ante = models.ForeignKey(Individuo, on_delete=models.CASCADE, related_name="acompa??ante", null=True, blank=True)
    actividad = HTMLField(null=True)
    origen = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name="ingresos_transporte")
    destino = models.ForeignKey(Localidad, on_delete=models.CASCADE, related_name="ingresos_transporte")
    #Vehiculo
    marca = models.CharField('Marca del Vehiculo', max_length=200)
    modelo = models.CharField('Modelo del Vehiculo', max_length=200)
    patente = models.CharField('Dominio', max_length=200)
    titular = models.CharField('Titular del Vehiculo', max_length=200)
    #Archivos
    permiso_nacional = models.FileField('Permiso Nacional de Circulacion', upload_to='ingresos/', null=True, blank=True)
    licencia_conducir = models.FileField('Licencia de Conducir', upload_to='ingresos/', null=True, blank=True)
    #Interno
    token = models.CharField('Token', max_length=50, default=token_ingreso, unique=True)
    fecha = models.DateTimeField('Fecha de registro', default=timezone.now)
    estado = models.CharField('Estado', choices=ESTADO_INGRESO, max_length=1, default='C')
    qrpath = models.CharField('qrpath', max_length=100, null=True, blank=True)
    def __str__(self):
        return str(self.chofer) + ', Vehiculo:' + self.marca + ' ' + self.modelo + ' ' + self.patente
    def listo(self):
        #Chequeamos que haya cargado permiso y licencia
        lista = (self.permiso_nacional is not None) and (self.licencia_conducir is not None)
        if lista:#Chequeamos que haya cargado Chofer
            lista = (self.chofer is not None)
        if lista:#Chequeamos que chofer tenga App
            lista = (self.chofer.appdata is not None)
        return lista
    def get_qr(self):
        if self.qrpath:
            return self.qrpath
        else:
            path = MEDIA_ROOT + '/circulacion/qrcode-'+str(self.id)+'.png'
            img = qrcode.make(self.token)#TIENE QUE SER URL A: redirect> 'permisos:ver_ingreso_aprobado' token=ingreso.token
            img.save(path)
            relative_path = 'archivos/circulacion/qrcode-'+ str(self.id)+'.png'
            self.qrpath = relative_path
            self.save()
            return self.qrpath
    def generar_pdf(self):  ##### AGREGAR QR
        packet = io.BytesIO()
        # Se crear un nuevo pdf utilizando ReportLab
        pdf = canvas.Canvas(packet, pagesize=A4)
        #escribimos textos del pdf
        #Fechamos
        pdf.setFont('Times-Roman', 9)
        pdf.drawString(475, 680, str(timezone.now())[0:16])
        #Armamos documento
        pdf.setFont('Times-Roman', 18)
        pdf.drawString(30, 650, "PERMISO DE CIRCULACION TEMPORAL")
        pdf.setFont('Times-Roman', 12)
        pdf.drawString(30, 630, "Tipo: " + self.get_tipo_display())
        pdf.drawString(30, 585, "Origen del Viaje: "+str(self.origen))
        pdf.drawString(30, 570, "Destino del Viaje: "+str(self.destino))
        pdf.drawString(30, 555, "Vehiculo: " + self.marca + " " + self.modelo + " - Patente" + self.patente)
        pdf.drawString(30, 540, "Actividad: " + strip_tags(self.actividad))
        #Datos del Chofer
        pdf.line(200, 520, 400, 520)
        pdf.drawString(30, 500, "Chofer: "+str(self.chofer))
        pdf.drawString(45, 485, "Telefono: "+ self.chofer.telefono)
        if self.acompa??ante:
            pdf.drawString(30, 460, "Chofer: "+str(self.acompa??ante))
            pdf.drawString(45, 445, "Telefono: "+ self.acompa??ante.telefono)
        try:
            #Agregamos licencia de conducir
            pdf.line(200, 420, 400, 420)
            pdf.drawString(30, 400, "Licencia de Conducir: ")
            pdf.drawImage(BASE_DIR+self.licencia_conducir.url, 50, 230, 75*mm, 50*mm)
        except:
            pass # No subio una imagen
        #Agregamos Codigo QR
        pdf.drawImage(self.get_qr(), 420, 520, 50*mm, 50*mm)
        #Grabamos el PDF
        pdf.save()
        packet.seek(0)
        nuevo_pdf = PdfFileReader(packet)
        # Leemos el pdf base
        existe_pdf = PdfFileReader(STATIC_ROOT+'/archivo/plantilla_nota.pdf', "rb")
        salida = PdfFileWriter()
        # Se agregan los datos de la persona que ser?? dada de alta, al pdf ya existente
        pagina = existe_pdf.getPage(0)
        pagina.mergePage(nuevo_pdf.getPage(0))
        salida.addPage(pagina)
        #Finalmente se escribe la salida, en un archivo real
        outputStream = open(MEDIA_ROOT+'/circulacion/'+self.token+".pdf", "wb")
        salida.write(outputStream)
        outputStream.close()  

class Emails_Circulacion(models.Model):
    circulacion = models.ForeignKey(CirculacionTemporal, on_delete=models.CASCADE, related_name="emails")
    fecha = models.DateTimeField('Fecha de Envio', default=timezone.now)
    asunto = models.CharField('Asunto', max_length=100)
    cuerpo = models.CharField('Cuerpo', max_length=1000)
    operador = models.ForeignKey(Operador, on_delete=models.CASCADE, related_name="circulacion_emailsenviados")

class RegistroCirculacion(models.Model):
    circulacion = models.ForeignKey(CirculacionTemporal, on_delete=models.CASCADE, related_name="registros")
    #Inicio
    control_inicio = models.IntegerField('Lugar de Control de Inicio', choices=FRONTERA_CONTROL, default=1)
    destino = models.ForeignKey(Localidad, on_delete=models.CASCADE, related_name="destino_transporte", null=True, blank=True)#Default=circulacion.destino
    cant_inicio = models.IntegerField('Cantidad Pasajeros', default=1)
    tiempo_permitido = models.IntegerField('Horas Permitidas', default=6)
    fecha_inicio = models.DateTimeField('Fecha de Inicio Circulacion', default=timezone.now)
    #Final
    control_final = models.IntegerField('Lugar de Control Final', choices=FRONTERA_CONTROL, null=True, blank=True)
    cant_final = models.IntegerField('Cantidad Pasajeros', default=1)
    aclaraciones = models.TextField('Aclaraciones en Salida', null=True, blank=True)
    fecha_final = models.DateTimeField('Fecha de Fin Circulacion', null=True, blank=True)
    #Interno
    tipo_alarma = models.CharField('Tipo Ingreso', choices=TIPO_ALARMA, max_length=2, default='SA')
    procesado = models.BooleanField('Procesada', default=False)
    class Meta:
        ordering = ('fecha_inicio', )
    def __str__(self):
        return str(self.circulacion) + ': ' + str(self.get_control_inicio_display()) + '(' + str(self.fecha_inicio)[0:16] + ')'
    def tiempo_real(self):
        if self.control_final:
            return (self.fecha_final - self.fecha_inicio).total_seconds() / 3600
        else:
            return self.tiempo_permitido - ((timezone.now() - self.fecha_inicio).total_seconds() / 3600)
    def geoposiciones(self):
        #Individuos a Seguir:
        num_docs = [p.num_doc for p in self.pasajeros.all()]
        #Obtener todas las geopos posibles:
        geoposiciones = GeoPosicion.objects.filter(individuo__num_doc__in=(num_docs))
        #Filtramos solo los items para ese recorrido
        geoposiciones = geoposiciones.filter(fecha__gte=self.fecha_inicio)
        if self.fecha_final:
            geoposiciones = geoposiciones.filter(fecha__lte=self.fecha_final)
        #Optimizamos
        return geoposiciones.select_related('individuo')

class PasajeroCirculacion(models.Model):
    registro = models.ForeignKey(RegistroCirculacion, on_delete=models.CASCADE, related_name="pasajeros")
    num_doc = models.CharField('Numero de Documento/Pasaporte', 
        max_length=50,
        validators=[RegexValidator('^[A-Z_\d]*$', 'Solo Mayusculas.')],
    )
    individuo = models.ForeignKey(Individuo, on_delete=models.SET_NULL, null=True, blank=True, related_name="registros")
    inicio = models.BooleanField('Ingreso Marcado', default=False)
    final = models.BooleanField('Salida Marcada', default=False)
    def get_individuo(self):
        try:
            return Individuo.objects.get(num_doc=self.num_doc)
        except Individuo.DoesNotExist:
            return None

if not LOADDATA:
    #Auditoria
    auditlog.register(Permiso)
    auditlog.register(NivelRestriccion)
    auditlog.register(IngresoProvincia)