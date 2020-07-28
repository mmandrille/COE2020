TIPO_SEGUIMIENTO = (
    ('I', 'Inclusion al Sistema'),
    ('A', 'Autodiagnostico'),
    ('AI', 'Actualizacion de Individuo'),
    ('IT', 'Inicio Tracking'),
    ('AT', 'Alerta Tracking'),
    ('FT', 'Finalizacion del Tracking'),
    ('DF', 'Domicilio Fuera de la Provincia'),
    ('TA', 'Traslado a Aislamiento'),
    ('RC', 'Registro de Circulacion Temporal'),
    #Todos los usuarios
    ('L', 'Llamada Telefonica'),
    ('M', 'Reporte Medico'),
    ('C', 'Cronologia'),
    ('E', 'Epicrisis'),
    ('IR', 'Individuo Sospechoso: Evaluar'),
    ('ET', 'Esperando Resultados PCR'),
    ('TE', 'No Posee Telefono / Telefono Equivocado'),
    ('PT', 'Pedido de Test'),
    ('FS', 'Fin del Seguimiento/Alta'),
    #Solo usuarios con permiso: 
    ('CT', 'Confirmado por Test'),
    ('DT', 'Descartado por Test'),
    ('AP', 'Alta de Positivo por PCR'),
)

def obtener_seguimientos(user):
    #Tipo de Seguimientos:
    sistema = ['I', 'A', 'IT', 'AT', 'FT', 'DF', 'TA', 'RC']
    publicos = ['L', 'M', 'C', 'E', 'IR', 'ET', 'TE','FS', 'PT']
    epidemiologia = ['CT', 'DT', 'AP']
    #Generamos seguimientos accesibles
    tipos = [t for t in TIPO_SEGUIMIENTO if t[0] in publicos]
    #Agregamos segun permisos:
    if user.has_perm('operadores.epidemiologia'):
        tipos += [t for t in TIPO_SEGUIMIENTO if t[0] in epidemiologia]
    if user.has_perm('operadores.sistemas'):
        tipos += [t for t in TIPO_SEGUIMIENTO if t[0] in sistema]
    return tipos

TIPO_VIGIA = (
    ('VE', 'Vigilancia Epidemiologica'),
    ('VM', 'Vigilancia Salud Mental'),
    ('AP', 'Atencion Psiquiatrica'),
    ('VD', 'Vigilancia de Sospechosos - Domestica'),
    ('ST', 'Vigilancia Medica'),
    ('VT', 'Vigilancia de Circulacion Temporal'),
)

ESTADO_OPERATIVO = (
    ('C', 'Creado'),
    ('I', 'Inicializado'),
    ('F', 'Finalizado'),
    ('E', 'Eliminado'),
)

ESTADO_RESULTADO = (
    ('E', 'Esperando Resultado'),
    ('P', 'Positivo'),
    ('N', 'Negativo'),
)

TIPO_TURNO = (
    ('M', 'MANIANA'),
    ('T', 'TARDE'),
    ('N', 'NOCHE'),
)