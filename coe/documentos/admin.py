#Imports Django
from django.contrib import admin
#Imports extras

#Imports de la app
from .models import Documento, Version

#Definimos los inlines:
class VersionInline(admin.TabularInline):
    model = Version
    fk_name = 'documento'
    def has_delete_permission(self, request, obj=None):
        return False

#Definimos nuestros modelos administrables:
class DocumentoAdmin(admin.ModelAdmin):
    model = Documento
    search_fields = ['nombre']
    list_filter = ['subcomite', ]
    inlines = [VersionInline]
    def has_delete_permission(self, request, obj=None):
        return False

# Register your models here.
admin.site.register(Documento, DocumentoAdmin)