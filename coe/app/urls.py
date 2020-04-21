#imports django
from django.urls import path
from django.conf.urls import url
#Import de modulos personales
from . import apps_views as apps_views
from . import app_apis as app_apis
from . import autocomplete


#Definimos paths de la app
app_name = 'app'
urlpatterns = [
    #App
    path('config', app_apis.AppConfig, name='AppConfig'),
    path('registro', app_apis.registro, name='registro'),
    path('foto_perfil', app_apis.foto_perfil, name='foto_perfil'),
    path('encuesta', app_apis.encuesta, name='encuesta'),
    path('start/tracking', app_apis.start_tracking, name='start_tracking'),
    path('tracking', app_apis.tracking, name='tracking'),
    path('salvoconducto', app_apis.pedir_salvoconducto, name='pedir_salvoconducto'),
    path('get/salvoconducto', app_apis.ver_salvoconducto, name='ver_salvoconducto'),
    path('control/salvoconducto', app_apis.control_salvoconducto, name='control_salvoconducto'),
    path('get/notificacion', app_apis.notificacion, name='notificacion'),
    #Testing
    path('send/notificacion', apps_views.enviar_notificacion, name='enviar_notificacion'),
    path('save/notificacion', apps_views.guardar_notificacion, name='enviar_notificacion'),
    #Descarga
    path('down_app', apps_views.download_app, name='download_app'),
    path('down_control', apps_views.download_control, name='download_control'),
    #Autocomplete:
    url(r'^appdata-autocomplete/$', autocomplete.AppDataAutocomplete.as_view(), name='appdata-autocomplete'),
    url(r'^dispositivo-autocomplete/$', autocomplete.DispositivoAutocomplete.as_view(), name='dispositivo-autocomplete'),
]