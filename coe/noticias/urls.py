from django.urls import path
#Import de modulos personales
from . import views

app_name = 'noticias'
urlpatterns = [
    path('', views.ver_noticias, name='ver_noticias'),
    path('<int:noticia_id>', views.ver_noticia, name='ver_noticia'),
    path('carousel', views.carousel, name='carousel'),

    path('buscar', views.buscar_noticias, name='buscar_noticias'),
    path('tags/<int:tag_id>', views.buscar_etiqueta, name='buscar_etiqueta'),

]