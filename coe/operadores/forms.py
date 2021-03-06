#Imports Python
from datetime import date
#Imports Django
from django.utils import timezone
from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import CheckboxSelectMultiple
#Imports extra
from dal import autocomplete
#Imports del proyecto
from core.widgets import XDSoftDatePickerInput
#Imports de la app
from .models import SubComite, Operador

#Definimos nuestros forms
class SubComiteForm(forms.ModelForm):
    class Meta:
        model = SubComite
        fields= '__all__'
        exclude = ('activo',)

class BuscarOperadorForm(forms.Form):
    operador = forms.ModelChoiceField(
        label='',
        queryset=Operador.objects.all(),
        widget=autocomplete.ModelSelect2(url='operadores:operadores-autocomplete')
    )

class CrearOperadorForm(forms.ModelForm):
    new_user = forms.BooleanField(label="Crear Usuario", initial=False, required=False)
    class Meta:
        model = Operador
        fields= '__all__'
        exclude = ('qrpath', 'usuario', 'individuo')
        widgets = {
            'subcomite': autocomplete.ModelSelect2(url='operadores:subcomite-autocomplete'),
        }

class ModOperadorForm(forms.ModelForm):
    username = forms.CharField(label='Usuario', max_length=15, min_length=6, required=False)
    permisos = forms.MultipleChoiceField(
        label='Permisos',
        widget=CheckboxSelectMultiple(attrs={'class':'multiplechoice',}),
        required=False,
    )
    class Meta:
        model = Operador
        fields= '__all__'
        exclude = ('qrpath', 'usuario', 'individuo')
        widgets = {
            'subcomite': autocomplete.ModelSelect2(url='operadores:subcomite-autocomplete'),
        }
    #Inicializacion
    def __init__(self, *args, **kwargs):
        #Obtenemos permisos
        permisos_list = kwargs.pop('permisos_list', None)
        if permisos_list:
            self.base_fields['permisos'].choices = [(p.id, p.name) for p in permisos_list]
        super(ModOperadorForm, self).__init__(*args, **kwargs)
    def clean_username(self):
        if not hasattr(self, 'instance') and User.objects.filter(username=self.cleaned_data['username']):
            raise forms.ValidationError("El usuario indicado ya esta en uso, si el usuario tiene mas de una funcion, contacte al administrador")
        return self.cleaned_data['username']
    def clean_email(self):
        if not hasattr(self, 'instance') and User.objects.filter(email=self.cleaned_data['email']):
            raise forms.ValidationError("El mail indicado ya esta en uso, si el usuario tiene mas de una funcion, contacte al administrador")
        return self.cleaned_data['email']

class ImprimirTarjetasForm(forms.Form):
    operadores = forms.MultipleChoiceField(
        label='Seleccione Operadores',
        choices=[],
        widget=CheckboxSelectMultiple(attrs={'class':'multiplechoice',}),
    )
    #Inicializacion
    def __init__(self, *args, **kwargs):
        #Obtenemos permisos
        self.base_fields['operadores'].choices = [(o.id, o.apellidos+', '+o.nombres ) for o in Operador.objects.all()]
        super(ImprimirTarjetasForm, self).__init__(*args, **kwargs)

class ModPassword(forms.Form):
    username = forms.CharField(label='Usuario', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    passwd1 = forms.CharField(label="Password", max_length=32, widget=forms.PasswordInput)
    passwd2 = forms.CharField(label="Repetir Password", max_length=32, widget=forms.PasswordInput)
    def clean_passwd2(self):
        passwd1 = self.cleaned_data['passwd1']
        passwd2 = self.cleaned_data['passwd2']
        if passwd1 != passwd2:
            raise forms.ValidationError("Las contrase??as no son iguales")
        return ''

class AuditoriaForm(forms.Form):
    usuario = forms.ModelChoiceField(
        label='Usuario',
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(url='core:usuarios-autocomplete'),
        required=True)
    begda = forms.DateField(label='Inicio', initial=timezone.now(), widget=XDSoftDatePickerInput())
    endda = forms.DateField(label='Fin',initial=timezone.now(), widget=XDSoftDatePickerInput())
    def __init__(self, *args, **kwargs):
        super(AuditoriaForm, self).__init__(*args, **kwargs)
        if kwargs.get('initial', None):
            if kwargs['initial'].get('usuario'):
                self.fields['usuario'].widget = forms.HiddenInput()

class AsistenciaForm(forms.Form):
    num_doc = forms.IntegerField(label='Num de Documento', required=False)
    widgets = {
        'num_doc': forms.TextInput(attrs={}),
    }
    def clean(self):
        #Buscamos si existe el operador
        try:           
            if self.cleaned_data['num_doc']:
                operador = Operador.objects.get(num_doc=self.cleaned_data['num_doc'])
        except Operador.DoesNotExist:
            raise forms.ValidationError('No existe Operador Autorizado con ese Documento de Identidad.')
        #Lo preparamos para futuro uso
        if operador:
            self.operador = operador
        return self.cleaned_data   
