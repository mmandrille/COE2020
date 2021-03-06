#Imports Django
from django.contrib import admin
#Imports extras
#Imports de la app
from .models import Acta, Participe

#Definimos los inlines:
class ParticipeInline(admin.TabularInline):
    model = Participe
    fk_name = 'acta'
    extra = 1

#Definimos nuestros modelos administrables:
class ActaAdmin(admin.ModelAdmin):
    model = Acta
    search_fields = ['nombre',]
    list_filter = ['tipo']
    inlines = [ParticipeInline]

# Register your models here.
admin.site.register(Acta, ActaAdmin)