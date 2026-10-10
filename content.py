"""Contenidos didácticos de apoyo: no son registros históricos del proyecto."""
LESSONS = [
    {
      'slug':'fundamentos','tag':'Conceptos básicos','title':'Educación Física y bienestar', 'time':'6 min', 'icon':'◎',
      'intro':'La Educación Física desarrolla habilidades motrices, conocimientos del cuerpo, convivencia y hábitos para la vida.',
      'sections':[
        ('¿Qué estudia la Educación Física?', 'Estudia el movimiento humano desde la enseñanza: coordinación, actividad física, prácticas recreativas y deportivas, autocuidado y colaboración.'),
        ('Aprender desde la experiencia', 'La práctica puede complementarse con explicaciones sobre cómo responde el organismo antes, durante y después del ejercicio. La tecnología ayuda a visualizar y registrar estas experiencias.'),
        ('Ejemplo de aula', 'Realiza una caminata suave y registra cómo te sientes antes y después. Relaciona la experiencia con respiración, esfuerzo y recuperación.')],
      'reference':'UNESCO (2015), citado en el trabajo de investigación.'
    },
    {
      'slug':'anatomia','tag':'Cuerpo humano','title':'Anatomía funcional y articulaciones','time':'8 min','icon':'◇',
      'intro':'Comprender músculos, huesos y articulaciones ayuda a explicar cómo se generan y coordinan los movimientos.',
      'sections':[
        ('Estructuras del movimiento', 'Los huesos proporcionan soporte, las articulaciones permiten distintos grados de movimiento y los músculos producen fuerza mediante contracción.'),
        ('Movimientos articulares', 'La flexión y la extensión cambian el ángulo entre segmentos del cuerpo. La abducción y la aducción describen movimientos respecto al eje corporal. Cada articulación tiene posibilidades propias.'),
        ('Actividad práctica', 'Observa de forma segura la flexión del codo y la extensión de la rodilla. Identifica qué segmentos se mueven. No fuerces el rango articular.')],
      'reference':'Contenido educativo complementario basado en el tema de anatomía funcional del proyecto.'
    },
    {
      'slug':'fisiologia','tag':'Ejercicio','title':'Fisiología del ejercicio','time':'8 min','icon':'♡',
      'intro':'Durante la actividad física cambian la respiración, la circulación sanguínea y las necesidades de energía.',
      'sections':[
        ('Respuesta cardiovascular', 'La frecuencia cardíaca es el número de latidos del corazón por minuto. Suele aumentar durante el ejercicio, aunque depende de la actividad y de características individuales.'),
        ('La recuperación', 'Después de la actividad, el organismo retorna progresivamente hacia condiciones de reposo. La recuperación y la hidratación son parte de la práctica responsable.'),
        ('Experimenta con una medición', 'Cuenta tus pulsaciones durante 15 segundos mientras estás en reposo y multiplica por cuatro. Registra el dato como una observación educativa, no como diagnóstico.')],
      'reference':'Contenido educativo complementario basado en la actividad de fisiología del ejercicio del documento.'
    },
    {
      'slug':'capacidades','tag':'Movimiento','title':'Capacidades físicas y evaluación motriz','time':'7 min','icon':'↗',
      'intro':'La fuerza, resistencia, velocidad, flexibilidad, equilibrio y coordinación se trabajan con actividades adecuadas a cada grupo.',
      'sections':[
        ('Capacidades y habilidades', 'Las capacidades físicas se expresan de distintas formas según la actividad. Las habilidades motrices implican aprender a ejecutar movimientos con control y adaptación.'),
        ('Registrar para aprender', 'El tiempo de carrera, la distancia de un salto o la duración de un equilibrio pueden observarse en diferentes fechas para reflexionar sobre las actividades.'),
        ('Interpretación responsable', 'Los resultados dependen de la edad, práctica, contexto y técnica. No deben emplearse para etiquetar a estudiantes ni emitir conclusiones clínicas.')],
      'reference':'Actividad didáctica complementaria del módulo de evaluación física.'
    },
    {
      'slug':'habitos','tag':'Autocuidado','title':'Hábitos de actividad física saludable','time':'6 min','icon':'✦',
      'intro':'La actividad física se acompaña de descanso, alimentación suficiente, hidratación, progresión y prácticas seguras.',
      'sections':[
        ('Antes de comenzar', 'Revisa el espacio, usa ropa cómoda, prepara el material y realiza movimientos progresivos apropiados al grupo.'),
        ('Durante la actividad', 'Prioriza la técnica, el respeto y la cooperación. Escucha señales de fatiga, dolor o malestar y comunica cualquier dificultad.'),
        ('Después de la sesión', 'Registra lo aprendido y reflexiona sobre las sensaciones del cuerpo. Evita utilizar mediciones corporales para comparaciones entre compañeros.')],
      'reference':'Contenido didáctico complementario del eje de hábitos saludables del proyecto.'
    },
    {
      'slug':'tecnologia','tag':'Innovación','title':'Tecnología en la Educación Física','time':'8 min','icon':'▣',
      'intro':'Los recursos digitales complementan la práctica motriz mediante información, interacción y representación visual.',
      'sections':[
        ('Página web educativa', 'Permite consultar materiales de anatomía, fisiología y fundamentos científicos antes o después de las actividades prácticas.'),
        ('Holograma didáctico', 'Las representaciones visuales tridimensionales simuladas permiten observar y discutir el movimiento articular. No sustituyen la actividad corporal.'),
        ('Códigos QR y aprendizaje', 'Los códigos permiten acceder a preguntas y recursos desde estaciones educativas. La práctica física se combina con reflexión y actividades colaborativas.')],
      'reference':'Terán (2026), propuesta transformadora, páginas 54–61.'
    },
]
ACTIVITIES = [
  {'slug':'pulso','name':'Reto: frecuencia cardíaca', 'intro':'Comprueba lo aprendido sobre pulsaciones y ejercicios.', 'questions':[
    {'question':'¿Cuántos segundos tiene un minuto?', 'options':['30','60','90'], 'answer':1, 'feedback':'Un minuto tiene 60 segundos.'},
    {'question':'Contaste 20 pulsaciones en 15 segundos. ¿Cuál es la frecuencia en latidos por minuto?', 'options':['80 lpm','35 lpm','120 lpm'], 'answer':0, 'feedback':'20 × (60 ÷ 15) = 80 lpm.'},
    {'question':'¿El pulso debe utilizarse para diagnosticar problemas de salud desde esta web?', 'options':['Sí','No'], 'answer':1, 'feedback':'Solo se utiliza con fines educativos y descriptivos.'},
  ]},
  {'slug':'movimiento','name':'Reto: movimiento articular', 'intro':'Relaciona las articulaciones con el movimiento.', 'questions':[
    {'question':'¿Qué ocurre cuando flexionas el codo?', 'options':['Disminuye el ángulo entre el brazo y el antebrazo','Siempre se detiene la respiración','Se alarga un hueso'], 'answer':0,'feedback':'La flexión del codo disminuye el ángulo entre segmentos.'},
    {'question':'¿Qué recurso del proyecto ayuda a visualizar movimientos articulares?', 'options':['Holograma didáctico','Hoja de asistencia','Boletín de notas'], 'answer':0, 'feedback':'El trabajo incluye una representación holográfica simulada.'},
  ]},
  {'slug':'salud','name':'Reto: hábitos saludables', 'intro':'Refuerza las buenas prácticas en Educación Física.', 'questions':[
    {'question':'¿Qué conducta es recomendable antes de una actividad?', 'options':['Ignorar el espacio','Preparar materiales y realizar calentamiento adecuado','Comparar cuerpos'], 'answer':1, 'feedback':'Prepararse ayuda a realizar actividades de manera segura.'},
    {'question':'¿Es correcto comparar públicamente el IMC de estudiantes?', 'options':['Sí','No'], 'answer':1, 'feedback':'Los datos antropométricos son privados y no se utilizan para etiquetar a compañeros.'},
  ]},
]
