#Imports Django
from django.contrib import admin
#Imports extras
from django.db import models
from django.forms import CheckboxSelectMultiple
#Imports del proyecto
#Imports de la app
from .models import Archivo
from .models import Enfermedad
from .models import Vehiculo, Individuo, Domicilio
from .models import Situacion, Relacion
from .models import Atributo
from .models import Sintoma
from .models import SubtipoLaboral

#Definimos los inlines:
class SituacionInline(admin.TabularInline):
    model = Situacion
    fk_name = 'individuo'
    extra = 0

class RelacionInline(admin.TabularInline):
    model = Relacion
    fk_name = 'individuo'
    extra = 0

class DomicilioInline(admin.TabularInline):
    model = Domicilio
    fk_name = 'individuo'
    extra = 0

class AtributoInline(admin.TabularInline):
    model = Atributo
    fk_name = 'individuo'
    extra = 0

class SintomaInline(admin.TabularInline):
    model = Sintoma
    fk_name = 'individuo'
    extra = 0

class IndividuoInline(admin.TabularInline):
    model = Individuo
    fk_name = 'individuo'
    extra = 1

#Definimos nuestros modelos administrables:
class ArchivoAdmin(admin.ModelAdmin):
    model = Archivo
    search_fields = ['nombre',]
    list_filter = ['tipo', ]

class EnfermedadAdmin(admin.ModelAdmin):
    model = Individuo
    search_fields = ['nombres', 'sintomas__nombre', ]
    def has_delete_permission(self, request, obj=None):
        return False
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

class IndividuoAdmin(admin.ModelAdmin):
    model = Individuo
    search_fields = ['nombres', 'apellidos', 'num_doc', ]
    list_filter = ['nacionalidad']
    inlines = [SituacionInline, RelacionInline, DomicilioInline, AtributoInline, SintomaInline, ]

class VehiculoAdmin(admin.ModelAdmin):
    model = Vehiculo
    search_fields = ['identificacion',]
    list_filter = ['tipo']


class SubtipoLaboralAdmin(admin.ModelAdmin):
    model = SubtipoLaboral
    search_fields = ['identificacion',]
    list_filter = ['tipo']

# Register your models here.
admin.site.register(Archivo, ArchivoAdmin)
admin.site.register(Enfermedad, EnfermedadAdmin)
admin.site.register(Individuo, IndividuoAdmin)
admin.site.register(Vehiculo, VehiculoAdmin)
admin.site.register(SubtipoLaboral, SubtipoLaboralAdmin)