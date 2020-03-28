#Import Django
from django.db import models
from django.utils import timezone
#Imports de la app
from .choices import TIPO_GRAFICO

# Create your models here.
class Grafico(models.Model):
    nombre = models.CharField('Nombre Informatico', max_length=100)
    verbose_name = models.CharField('Nombre Para Mostrar', max_length=100)
    tipo = models.CharField('Tipo Grafico', choices=TIPO_GRAFICO, max_length=1, default='L')
    update = models.DateField('Ultimo Dato Cargado', null=True)
    columnas = models.CharField('Columnas a Mostrar', max_length=250, null=True)
    publico = models.BooleanField(default=False)
    def __str__(self):
        return self.nombre + ': ' + str(self.update)
    def agregar_dato(self, update_date, columna, fila, valor):
        #Eliminamos si tenemos que remplazar
        self.datos.filter(columna=columna, fila=fila).delete()
        #Agregamos el dato:
        dato = Dato()
        dato.grafico = self
        dato.columna = columna
        dato.fila = fila
        dato.valor = valor
        dato.save()
        #Informamos que fue Actualizado
        self.update = update_date
        self.save()
    def cabecera(self):
        #Obtenemos todo lo necesario para procesar
        if self.columnas:
            return ['Fecha'] + self.columnas.split(';')
        else:
            return ['Fecha'] + list(self.datos.values_list('columna', flat=True).distinct())
    def obtener_datos(self):
        #Obtenemos todo lo necesario para procesar
        columnas = self.cabecera()[1:]
        #Referencias disponibles
        filas = list(self.datos.order_by('id').values_list('fila', flat=True).distinct())
        #Traemos todo el bloque de datos ya indexado
        dict_datos = {(d.columna,d.fila):d for d in self.datos.all()}
        #Creamos nuestro vector
        datos = []
        for fila in filas:#Por cada Fecha
            #Generamos cada linea
            dato = []
            for columna in columnas:
                dato.append(dict_datos[(columna, fila)])
            #Agregamos la linea
            datos.append(dato)
        return datos

class Dato(models.Model):
    grafico = models.ForeignKey(Grafico, on_delete=models.CASCADE, related_name="datos")
    columna = models.CharField('columna', max_length=50)
    fila = models.CharField('Fila', max_length=100, null=True)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    def __str__(self):
        return self.fila + '-' + self.columna + ' Cant: ' + str(self.valor) 
