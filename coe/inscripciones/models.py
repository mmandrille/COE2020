#Imports de Django
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
#Imports extras
from tinymce.models import HTMLField
#Imports del proyecto
from core.choices import TIPO_DOCUMENTOS
from georef.models import Localidad
from informacion.models import Individuo
#Imports de la app
from .choices import TIPO_INSCRIPTO, GRUPO_SANGUINEO, TIPO_PROFESIONAL

# Create your models here.
class Area(models.Model):
    nombre = models.CharField('Nombres', max_length=250)
    orden = models.IntegerField('Prioridad')
    def __str__(self):
        return self.nombre

class Tarea(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name="tareas")
    nombre = models.CharField('Nombres', max_length=250)
    orden = models.IntegerField('Prioridad')
    def __str__(self):
        return self.nombre

class Inscripto(models.Model):
    tipo_inscripto = models.CharField(choices=TIPO_INSCRIPTO, max_length=2, default='PS')
    tipo_doc = models.IntegerField(choices=TIPO_DOCUMENTOS, default=2, blank=True)
    num_doc = models.CharField('Documento/Pasaporte', 
        max_length=20,
        validators=[RegexValidator('^[A-Z_\d]*$', 'Solo Mayusculas.')],
        unique=True,
    )
    apellidos = models.CharField('Apellidos', max_length=100)
    nombres = models.CharField('Nombres', max_length=100)
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento")
    profesion = models.IntegerField('Profesion', choices=TIPO_PROFESIONAL, null=True, blank=True)
    matricula = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField('Correo Electronico')
    domicilio = models.CharField('Domicilio', max_length=200)
    localidad = models.ForeignKey(Localidad, on_delete=models.CASCADE, null=True, blank=True)
    telefono = models.CharField('Telefono', max_length=20, default='+549388')
    archivo_dni = models.FileField('Foto DNI', upload_to='inscripciones/documentos/')
    archivo_titulo = models.FileField('Foto Titulo', upload_to='inscripciones/titulo/', null=True, blank=True)
    oficio = models.CharField("Profesion u Oficio", max_length=100, null=True, blank=True)
    info_extra = HTMLField(null=True, blank=True)
    grupo_sanguineo = models.IntegerField('Grupo Sanguineo', choices=GRUPO_SANGUINEO, null=True, blank=True)
    fecha = models.DateTimeField('Fecha Inscripcion', default=timezone.now)
    valido = models.BooleanField(default=False)
    individuo = models.ForeignKey(Individuo, on_delete=models.CASCADE, null=True, blank=True, related_name="voluntarios")
    disponible = models.BooleanField(default=True)
    def __str__(self):
        return self.apellidos + ', ' + self.nombres
    def as_dict(self):
        return {
            'id': self.id,
            'tipo_doc': self.get_tipo_doc_display(),
            'num_doc': self.num_doc,
            'apellidos': self.apellidos,
            'nombres': self.nombres,
            'profesion': self.get_profesion_display(),
            'matrícula': self.matricula,
            'email': self.email,
            'telefono': self.telefono,
            'archivo_dni': str(self.archivo_dni),
            'archivo_título': str(self.archivo_titulo),
            'info_extra': self.info_extra,
            'fecha': str(self.fecha),
            'valido': self.valido,
            'disponible': self.disponible,
        }

class TareaElegida(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name="elecciones")
    inscripto = models.ForeignKey(Inscripto, on_delete=models.CASCADE, related_name="elecciones")
