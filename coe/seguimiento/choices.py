TIPO_SEGUIMIENTO = (
    ('I', 'Inclusion al Sistema'),
    ('L', 'Llamada Telefonica'),
    ('M', 'Reporte Medico'),
    ('C', 'Cronologia'),
    ('E', 'Epicrisis'),
    ('PT', 'Pidio Test'),
    ('ET', 'Esperando Resultados'),
    ('CT', 'Confirmado por Test'),
    ('DT', 'Descartado por Test'),
    ('A', 'Autodiagnostico'),
    ('FS', 'Fin del Seguimiento/Alta'),
    ('IT', 'Inicio Tracking'),
    ('AT', 'Alerta Tracking'),
    ('FT', 'Finalizacion del Tracking'),
    ('TA', 'Traslado a Aislamiento'),
    ('DF', 'Domicilio Fuera de la Provincia'),
    ('TE', 'No Posee Telefono / Telefono Equivocado'),
)

TIPO_VIGIA = (
    ('E', 'Vigilancia Epidemiologica'),
    ('M', 'Salud Mental'),
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