#Imports Django
from django.contrib import admin
#Imports de la app
from .models import Area, Tarea, Inscripcion

#Inline
class TareaInline(admin.TabularInline):
    model = Tarea
    fk_name = 'area'

#Definimos nuestros modelos administrables:
class AreaAdmin(admin.ModelAdmin):
    model = Area
    search_fields = ['nombre', ]
    inlines = [TareaInline]

class InscripcionAdmin(admin.ModelAdmin):
    model = Inscripcion
    search_fields = ['num_doc', 'apellidos', 'nombres',]
    list_filter = ['profesion', 'valido', 'disponible']

# Register your models here.
admin.site.register(Area, AreaAdmin)
admin.site.register(Inscripcion, InscripcionAdmin)