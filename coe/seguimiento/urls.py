#imports django
from django.conf.urls import url
from django.urls import path
#Import de modulos personales
from . import views as views
from . import autocomplete

#Definimos paths de la app
app_name = 'seguimiento'
urlpatterns = [
    #Publico:
    path('alta', views.buscar_alta_aislamiento, name='buscar_alta_aislamiento'),
    #Menu
    path('', views.menu_seguimiento, name='menu_seguimiento'),
    #Base
    path('lista/seguimientos', views.lista_seguimientos, name='lista_seguimientos'),
    path('ver/<int:individuo_id>', views.ver_seguimiento, name='ver_seguimiento'),
    #Lista Para Liberar:
    path('lista/esperando/alta', views.esperando_alta_seguimiento, name='esperando_alta_seguimiento'),
    path('dar/alta/<int:individuo_id>', views.dar_alta, name='dar_alta'),
    path('lista/altas/realizadas', views.altas_realizadas, name='altas_realizadas'),
    #Seguimiento
    path('cargar/seguimiento/<int:individuo_id>', views.cargar_seguimiento, name='cargar_seguimiento'),
    path('cargar/seguimiento/<int:individuo_id>/tipo/<str:tipo>', views.cargar_seguimiento, name='cargar_seguimiento'),
    path('mod/seguimiento/<int:individuo_id>/<int:seguimiento_id>', views.cargar_seguimiento, name='mod_seguimiento'),
    path('del/seguimiento/<int:seguimiento_id>', views.del_seguimiento, name='del_seguimiento'),
    #Administracion
    path('lista/vigias', views.lista_vigias, name='lista_vigias'),
    path('agregar/vigia', views.agregar_vigia, name='agregar_vigia'),
    path('del/vigia/<vigia_id>', views.del_vigia, name='del_vigia'),
    path('lista/sin/vigias', views.lista_sin_vigias, name='lista_sin_vigias'),
    #Otros Listados
    path('lista/autodiagnosticos', views.lista_autodiagnosticos, name='lista_autodiagnosticos'),
    path('lista/aislados', views.lista_aislados, name='lista_aislados'),
    #Panel
    path('panel/vigia', views.panel_vigia, name='mi_panel'),
    path('panel/vigia/<int:vigia_id>', views.panel_vigia, name='ver_panel'),
    path('agregar/vigilado/<int:vigia_id>', views.agregar_vigilado, name='agregar_vigilado'),
    path('quitar/vigilado/<int:vigia_id>/<int:individuo_id>', views.quitar_vigilado, name='quitar_vigilado'),
    #Autocomplete
    url(r'^individuosvigilados-autocomplete/$', autocomplete.IndividuosVigiladosAutocomplete.as_view(), name='individuosvigilados-autocomplete',),
    url(r'^vigias-autocomplete/$', autocomplete.VigiasAutocomplete.as_view(), name='vigias-autocomplete',),
]