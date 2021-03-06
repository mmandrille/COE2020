#Imports Django
from django.contrib import admin
#Imports de la app
from .models import Area, Tarea, Capacitacion, Inscripcion
from .models import PeticionCoca

#Inline
class TareaInline(admin.TabularInline):
    model = Tarea
    fk_name = 'area'

#Definimos nuestros modelos administrables:
class CapacitacionAdmin(admin.ModelAdmin):
    model = Capacitacion
    search_fields = ['nombre', ]

class AreaAdmin(admin.ModelAdmin):
    model = Area
    search_fields = ['nombre', ]
    inlines = [TareaInline]

class InscripcionAdmin(admin.ModelAdmin):
    model = Inscripcion
    search_fields = ['num_doc', 'apellidos', 'nombres',]
    list_filter = ['profesion', 'valido', 'disponible']

class PeticionPAdmin(admin.ModelAdmin):
    model = PeticionCoca
    list_filter = ['estado', 'fecha', 'destino']
    search_fields = ['individuos__apellidos', 'individuos__num_doc']

# Register your models here.
admin.site.register(Area, AreaAdmin)
admin.site.register(Capacitacion, CapacitacionAdmin)
admin.site.register(Inscripcion, InscripcionAdmin)
admin.site.register(PeticionCoca, PeticionPAdmin)
