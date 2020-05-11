#Imports Django
from django import forms
from django.utils import timezone
from django.forms.widgets import CheckboxSelectMultiple
#Imports extra
from dal import autocomplete
#Imports del proyecto
from coe.settings import SECRET_KEY
from core.widgets import XDSoftDatePickerInput, XDSoftDateTimePickerInput
from georef.models import Localidad, Ubicacion
#Imports de la app
from .choices import TIPO_ATRIBUTO, TIPO_SINTOMA
from .models import Vehiculo, TrasladoVehiculo
from .models import Individuo, Domicilio, SignosVitales, Atributo, Sintoma
from .models import Situacion, Archivo, Relacion
from .models import Documento

#Definimos nuestros forms
class ArchivoForm(forms.ModelForm):
    class Meta:
        model = Archivo
        fields = ['tipo', 'nombre', 'archivo', ]

class ArchivoFormWithPass(forms.ModelForm):
    passwd = forms.CharField(label="Password de Administrador", max_length=100, widget=forms.PasswordInput)
    class Meta:
        model = Archivo
        fields = ['tipo', 'nombre', 'archivo', ]
    def clean(self):
        if self.cleaned_data['passwd'] == SECRET_KEY:
            return self.cleaned_data
        else:
            raise forms.ValidationError("La contraseña ingresada es incorrecta.")

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields= '__all__'
        exclude = ('fecha', 'usuario',)

class TrasladoVehiculoForm(forms.ModelForm):
    class Meta:
        model = TrasladoVehiculo
        fields= '__all__'
        exclude = ('vehiculo', )
        widgets = {
            'fecha': XDSoftDateTimePickerInput(attrs={'autocomplete':'off'}),
        }

class IndividuoForm(forms.ModelForm):
    dom_localidad = forms.ModelChoiceField(
        queryset=Localidad.objects.all(),
        widget=autocomplete.ModelSelect2(url='georef:localidad-autocomplete'),
        required=False,
    )
    dom_calle = forms.CharField(required=False, )
    dom_numero = forms.CharField(required=False, )
    dom_aclaracion = forms.CharField(required=False, )
    dom_fecha = forms.DateTimeField(required=False)
    dom_aislamiento = forms.BooleanField(required=False, initial=False)
    atributos = forms.MultipleChoiceField(
        choices=TIPO_ATRIBUTO,
        widget=CheckboxSelectMultiple(attrs={'class':'multiplechoice',}),
        required=False
    )
    sintomas = forms.MultipleChoiceField(
        choices=TIPO_SINTOMA,
        widget=CheckboxSelectMultiple(attrs={'class':'multiplechoice',}),
        required=False
    )
    class Meta:
        model = Individuo
        fields= '__all__'
        exclude = ('seguimiento_actual', 'fotografia', 'qrpath', )
        widgets = {
            'fecha_nacimiento': XDSoftDatePickerInput(attrs={'autocomplete':'off'}),
            'nacionalidad': autocomplete.ModelSelect2(url='georef:nacionalidad-autocomplete'),
            'origen': autocomplete.ModelSelect2(url='georef:nacionalidad-autocomplete'),
            'destino': autocomplete.ModelSelect2(url='georef:localidad-autocomplete'),
            #Oculto
            'dom_fecha': forms.HiddenInput(),
            'dom_aislamiento': forms.HiddenInput(),
            'dom_ubicacion': forms.HiddenInput(),
        }
    #def __init__(self, *args, **kwargs):
    #    super(IndividuoForm, self).__init__(*args, **kwargs)
    #Si tiene domicili actual poner estos campos en NO EDITABLES    

class InquilinoForm(forms.ModelForm):
    atributos = forms.MultipleChoiceField(
        choices=TIPO_ATRIBUTO,
        widget=CheckboxSelectMultiple(attrs={'class':'multiplechoice',}),
        required=False
    )
    sintomas = forms.MultipleChoiceField(
        choices=TIPO_SINTOMA,
        widget=CheckboxSelectMultiple(attrs={'class':'multiplechoice',}),
        required=False
    )
    ubicacion = forms.ModelChoiceField(queryset=Ubicacion.objects.all(), required=True)
    habitacion = forms.CharField(label="Habitacion", required=True)
    fecha = forms.DateTimeField(label="Fecha Ingreso", required=True, 
        initial=timezone.now(),
        widget=XDSoftDateTimePickerInput()
    )
    class Meta:
        model = Individuo
        fields= '__all__'
        exclude = ('seguimiento_actual', 'fotografia', 'qrpath', )
        widgets = {
            'fecha_nacimiento': XDSoftDatePickerInput(attrs={'autocomplete':'off'}),
            'nacionalidad': autocomplete.ModelSelect2(url='georef:nacionalidad-autocomplete'),
            'origen': autocomplete.ModelSelect2(url='georef:nacionalidad-autocomplete'),
            'destino': autocomplete.ModelSelect2(url='georef:localidad-autocomplete'),
        }

class BuscadorIndividuosForm(forms.Form):
    nombre = forms.CharField(label="Nombre", required=False)
    apellido = forms.CharField(label="Apellido", required=False)
    calle = forms.CharField(label="Calle", required=False)
    localidad = forms.ModelChoiceField(
        queryset=Localidad.objects.all(),
        widget=autocomplete.ModelSelect2(url='georef:localidad-autocomplete'),
        required=False,
    )
    def clean(self):
        cant = 0
        #Vemos si aportaron datos
        if self.cleaned_data['nombre']: cant+=1
        if self.cleaned_data['apellido']: cant+=1
        if self.cleaned_data['calle']: cant+=1
        if self.cleaned_data['localidad']: cant+=1
        #Exigimos al menos 2 datos
        if cant < 2:
            raise forms.ValidationError("Debe ingresar al menos dos datos.")
        else:
            return self.cleaned_data

class BuscarIndividuoSeguro(forms.Form):
    num_doc = forms.CharField(label="Num Doc", required=True)
    apellido = forms.CharField(label="Apellido", required=True)

class SearchVehiculoForm(forms.Form):
    identificacion = forms.CharField(label="Patente/Identificacion", required=True)

class SearchIndividuoForm(forms.Form):
    num_doc = forms.CharField(label="Documento/Pasaporte", required=True)

class TrasladarIndividuoForm(forms.Form):
    habitacion = forms.CharField(label="Habitacion", required=True)
    fecha = forms.DateTimeField(label="Fecha Ingreso", required=True, 
        initial=timezone.now(),
        widget=XDSoftDateTimePickerInput()
    )

class DomicilioForm(forms.ModelForm):
    class Meta:
        model = Domicilio
        fields = '__all__'
        exclude = ('individuo', 'ubicacion')
        widgets = {
            'localidad': autocomplete.ModelSelect2(url='georef:localidad-autocomplete'),
        }

class SituacionForm(forms.ModelForm):
    class Meta:
        model = Situacion
        fields = '__all__'
        exclude = ('individuo', )
        widgets = {
            'fecha': XDSoftDateTimePickerInput(attrs={'autocomplete':'off'}),
        }

class SignosVitalesForm(forms.ModelForm):
    class Meta:
        model = SignosVitales
        fields = '__all__'
        exclude = ('individuo', )
        widgets = {
            'fecha': XDSoftDateTimePickerInput(attrs={'autocomplete':'off'}),
        }
    def __init__(self, *args, **kwargs):
        self.nolabel = ['', ]
        self.alinear = [('tension_sistolica', 'tension_diastolica'), ]
        super(SignosVitalesForm, self).__init__(*args, **kwargs)

class RelacionForm(forms.ModelForm):
    class Meta:
        model = Relacion
        fields= '__all__'
        exclude = ('individuo', )
        widgets = {
            'relacionado': autocomplete.ModelSelect2(url='informacion:individuos-autocomplete'),
        }

class AtributoForm(forms.ModelForm):
    class Meta:
        model = Atributo
        fields= '__all__'
        exclude = ('individuo', 'activo', )
        widgets = {
            'fecha': XDSoftDateTimePickerInput(attrs={'autocomplete':'off'}),
        }

class SintomaForm(forms.ModelForm):
    class Meta:
        model = Sintoma
        fields= '__all__'
        exclude = ('individuo', )
        widgets = {
            'fecha': XDSoftDateTimePickerInput(attrs={'autocomplete':'off'}),
        }

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields= '__all__'
        exclude = ('individuo', 'activo')
        widgets = {
            'fecha': XDSoftDateTimePickerInput(attrs={'autocomplete':'off'}),
        }

class ReporteHotelesForm(forms.Form):
    begda = forms.DateField(label="Ingreso Minimo", required=True, 
        initial=timezone.now(),
        widget=XDSoftDatePickerInput()
    )
    endda = forms.DateField(label="Ingreso Maxima", required=True, 
        initial=timezone.now(),
        widget=XDSoftDatePickerInput()
    )