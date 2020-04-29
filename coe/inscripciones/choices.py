#Choices
TIPO_INSCRIPTO = (
    ('PS', 'Profesionales de Salud'),
    ('VS', 'Voluntarios Sociales'),
)

ESTADO_INSCRIPTO = (
    (0, 'Inscripcion Iniciada'),
    (1, 'Inscripcion Terminada - Esperando Aprobacion'),
    (2, 'Pre Inscripcion Aprobada'),
    (3, 'Llamada Telefonica Aprobada'),
    (4, 'Tarea Asignada'),
)

GRUPO_SANGUINEO = (
    (1, 'A+'),
    (2, 'A-'),
    (3, 'B+'),
    (4, 'B-'),
    (5, 'AB+'),
    (6, 'AB-'),
    (7, '0+'),
    (8, '0-'),
)

TIPO_PROFESIONAL = (
    (1, 'Enfermeros profesionales'),
    (11, 'Auxiliares de enfermería'),
    (12, 'Licenciados de enfermería'),
    (2, 'Médicos de todas las especialidades'),
    (21, 'Técnicos radiólogos'),
    (22, 'Técnicos de farmacia'),
    (3, 'Farmacéuticos'),
    (4, 'Técnicos en emergencia'),
    (5, 'Técnicos de laboratorio'),
    (6, 'Bioquímicos'),
    (7, 'Kinesiólogos especializados en pacientes respiratorios'),
    (81, 'Educadores de la salud'),
    (82, 'Trabajador Social'),
    (91, 'Psicologos'),
    (92, 'Psiquiatra'),
    (99, 'Estudiantes de Carreras de Ciencias de la Salud'),
)

TIPO_DISPOSITIVO = (
    ('DK', 'Computadora de Escritorio'),
    ('NB', 'Notebook'),
    ('TC', 'Telefono Celular'),
    ('TF', 'Telefono Fijo'),
    ('TB', 'Tablet'),
)