#Imports Django
from django.apps import AppConfig
from django.db import OperationalError
#Imports del Proyecto
from coe.settings import DEBUG
from core.functions import agregar_menu

class GeotrackingConfig(AppConfig):
    name = 'geotracking'
    def ready(self):
        agregar_menu(self)
        #Tareas Background:
        try:
            if not DEBUG:
                from background_task.models import Task
                if not Task.objects.filter(verbose_name="geotrack_sin_actualizacion").exists():
                    from geotracking.tasks import geotrack_sin_actualizacion
                    geotrack_sin_actualizacion(repeat=3600 * 6, verbose_name="geotrack_sin_actualizacion")#Cada una hora
                if not Task.objects.filter(verbose_name="finalizar_geotracking").exists():
                    from geotracking.tasks import finalizar_geotracking
                    finalizar_geotracking(repeat=3600*12, verbose_name="finalizar_geotracking")#Cada 12 horas
        except OperationalError:
            pass #Por si no existe