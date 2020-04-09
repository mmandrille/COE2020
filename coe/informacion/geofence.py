#Imports de Django
from django.core.cache import cache
#Imports Extras
from geographiclib.geodesic import Geodesic
#Imports de la app
from .models import GeoPosicion, Seguimiento

#Definimos nuestras funciones:
def obtener_base(num_doc):
    geopos_bases = cache.get("geopos_bases")
    try:
        return geopos_bases[num_doc]
    except:
        try:
            gps = GeoPosicion.objects.get(
                    domicilio__individuo__num_doc=num_doc, 
                    aclaracion__icontains="INICIO TRACKING")
            if not geopos_bases:#Creamos la base inicial
                geopos_bases = {g.domicilio.individuo.num_doc: g for g in GeoPosicion.objects.filter(aclaracion="INICIO TRACKING")}
            geopos_bases[num_doc] = gps
            cache.set("geopos_bases", geopos_bases)
            return geopos_bases[num_doc]
        except GeoPosicion.DoesNotExist:
            return None

def controlar_distancia(nueva_geopos):
    #Obtenemos su posicion Permitida
    gps_base = obtener_base(nueva_geopos.domicilio.individuo.num_doc)
    #Calculamos diferencia
    geodesic = Geodesic.WGS84.Inverse(gps_base.latitud, gps_base.longitud, nueva_geopos.latitud, nueva_geopos.longitud)
    distancia = geodesic['s12']# en metros
    if distancia > 50:#Si tiene mas de 50 metros
        seguimiento = Seguimiento()
        seguimiento.individuo = gps_base.domicilio.individuo
        seguimiento.tipo = 'AT'
        seguimiento.aclaracion = 'Distancia: '+str(distancia)+'mts | '+str(nueva_geopos.fecha)
        seguimiento.save()
    return distancia