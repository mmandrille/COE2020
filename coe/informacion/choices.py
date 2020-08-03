#Choice Fields
TIPO_IMPORTANCIA = (
    (0, 'Nula'),
    (1, 'Baja'),
    (2, 'Intermedia'),
    (3, 'Alta'),
)

TIPO_ARCHIVO = (
    (1, 'Acta Pasajeros'),
    (2, 'Informe Externo'),
    (3, 'Informe Particular'),
    (4, 'Denuncia'),
    (5, 'Carga Masiva Same'),
    (6, 'Carga Masiva Epidemiologia'),
    (7, 'Carga Masiva Padron Individuos'),
    (7, 'Carga Masiva Padron Domicilios'),
)

TIPO_VEHICULO = (
    (1, 'Transporte Sanitario'),
    (2, 'Particular'),
    (3, 'Colectivo'),
    (4, 'Traffic'),
    (5, 'Comercial Pequeño'),
    (6, 'Avion'),
    (9, 'Cazador 360'),
)

TIPO_ESTADO = (
    (10, 'Sano'),
    (11, 'Asintomatico'),
    (31, 'Contacto Bajo Riesgo'),
    (32, 'Contacto Alto Riesgo'),
    (40, 'Sospechoso'),
    (50, 'Confirmado'),
    (2, 'Curado'),
    (1, 'Fallecido'),
    (0, 'Fuera del Territorio'),
)

TIPO_CONDUCTA = (
    ('A', 'Nada'),
    ('B', 'Evaluar'),
    ('C', 'Cuarentena Voluntaria'),
    ('D', 'Cuarentena Obligatoria (Domiciliario)'),
    ('E', 'Aislamiento (Custodiado)'),
    ('F', 'En Morgue'),
    ('G', 'Cremado'),
    ('H', 'Enterrado'),
)

TIPO_RELACION = (
    ('F', 'Familiar'),
    ('CE', 'Contacto Bajo Riesgo'),
    ('CA', 'Contacto Alto Riesgo'),
    ('MD', 'Mismo Domicilio'),
    ('O', 'Otro...'),
)

TIPO_ATRIBUTO = (
    #Vigilancia
    ('VE', 'Vigilancia Epidemiologica'),
    ('VM', 'Vigilancia Salud Mental'),
    ('AP', 'Atencion Psiquiatrica'),
    ('ST', 'Seguimiento Medico'),
    ('VD', 'Vigilancia Adultos Mayores'),
    ('VT', 'Vigilancia de Circulacion Temporal'),
    #Trabajo:
    ('AS', 'Es Agente de Salud'),
    ('PS', 'Es Personal de Seguridad'),
    ('FP', 'Es Funcionario Publico'),
    ('EP', 'Es Empleado Publico'),
    ('TE', 'Es Trabajador de Empresa Estrategica'),
    ('CT', 'Posee Permiso de Circulacion Temporal'),
    ('PD', 'Se encuentra Presos/Detenidos'),
    #Otros
    ('CE', 'Visito Pais de Riesgo/Contacto con Extranjeros'),
    ('CP', 'Tiene Potestad de Controlar Permisos'),
    ('VA', 'Voluntario Aprobado'),
    ('TO', 'Posee Obra Social'),
    ('TP', 'Test Prioritario'),
    ('PR', 'Poblacion de Riesgo/Comorbilidades'),
    ('DE', 'Denuncia Externa'),
    #excepciones (3 caracteres)
    ('OP2', 'Puede acreditar que requiere imprescindiblemente cuidados domiciliarios'),
    ('EMB', 'Embarazada a partir del segundo Trimestre'),
    ('DIS', 'Posee Certificado de Discapacidad'),
    ('APS', 'Posee antecedentes Psiquiatricos'),
    ('NM2', 'Grupo Familiar con menores de 2 años, adultos mayores y/o personas con discapacidad'),
)

def obtener_atributos(user):
    #Tipo de Seguimientos:
    publicos = ['OP2', 'EMB', 'DIS', 'APS', 'NM2']
    carga = ['CE', 'CP', 'TO', 'TP', 'PR', 'DE']
    ocupacion = ['AS', 'PS', 'FP', 'EP', 'TE', 'CT', 'PD']
    vigilancia = ['VE', 'VM', 'AP', 'ST', 'VT', 'VD']
    sistema = ['VA']
    
    #Generamos seguimientos accesibles
    tipos = [t for t in TIPO_ATRIBUTO if t[0] in publicos]
    #Agregamos segun permisos:
    
    if user.has_perm('operadores.sistemas'):#No existe, solo root
        tipos += [t for t in TIPO_ATRIBUTO if t[0] in sistema]
    return tipos

def atributos_iniciales():
    return [a for a in TIPO_ATRIBUTO if len(a[0]) == 2]

def atributos_excepcionales():
    return [a for a in TIPO_ATRIBUTO if len(a[0]) == 3]

TIPO_SINTOMA = (
    ('DPR', 'Dificultad para Respirar'),
    ('DM', 'Dolor Muscular'),
    ('DRO', 'Dolor RetroOcular'),
    ('ART', 'Dolor de Articulaciones'),
    ('DC', 'Dolor de Cabeza'),
    ('DG', 'Dolor de Garganta'),
    ('DP', 'Dolor de Pecho'),
    ('DSV', 'Dolor parte Superior del Vientre'),
    ('FAT', 'Fatiga'),
    ('FIE', 'Fiebre'),
    ('HEP', 'Hemorragia Profusa'),
    ('IO', 'Inflamacion de los Ojos'),
    ('MAR', 'Mareos'),
    ('NAS', 'Nauseas'),
    ('PAL', 'Palidez'),
    ('PDA', 'Perdida de Apetito'),
    ('RCA', 'Ritmo Cardiaco Acelerado'),
    ('SAR', 'Sarpullido'),
    ('SRM', 'Sarpullido Rojo con Manchas en la Piel'),
    ('SN', 'Secrecion Nasal'),
    ('TOS', 'Tos'),
    ('VOM', 'Vomitos'),
    ('ESC', 'Escalofrios'),
)

TIPO_PATOLOGIA = (
    ('HIP', 'HiperTension'),
    ('DBT', 'Diabetes'),
    ('TBC', 'Tuberculosis'),
    ('ASM', 'Asma'),
    ('CRD', 'Problemas Cardiacos'),
    ('CNR', 'Cancer'),
    ('END', 'Problemas Endocrinologicos'),
    ('EPC', 'EPOC'),
    ('ACV', 'Accidentes Cerebro Vasculares'),
    ('CLC', 'Celiacos'),
    ('TSM', 'Trastornos de Salud Mental'),
)

TIPO_DOCUMENTO = (
    ('HM', 'Historia Medica'),
    ('RG', 'Radiografia'),
    ('EC', 'Electrocardiograma'),
    ('AS', 'Analisis de Sangre'),
    ('AO', 'Analisis de Orina'),
    ('LB', 'Laboratorio'),
    ('AC', 'Certificado de Alta de Cuarentena'),
    ('TN', 'Certificado de Test Negativo'),
    ('CT', 'Certificado Temporal de Aislamiento en Domicilio'),
    ('FP', 'Foto de Perfil'),
    ('DI', 'Documento de Identidad'),
    ('LC', 'Licencia de Conducir'),
    ('PN', 'Permiso de Circulacion Nacional'),
    ('AT', 'Autorizacion Voluntariado - Tutor'),
    ('TP', 'Titulo Profesional'),
    ('OT', 'Otros'),
)