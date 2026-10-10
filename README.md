# EF+ · Plataforma de Educación Física

Aplicación **funcional y sencilla** creada con **Python 3, HTML, CSS, JavaScript básico y SQLite**. No usa frameworks web, npm, Docker, servidores de pago ni servicios externos. El código QR utiliza una biblioteca pequeña empaquetada localmente (licencia BSD).

Inspirada en el trabajo de investigación de la **Lcda. Rosanny A. Terán V.** sobre vinculación de la tecnología en la enseñanza de la Educación Física, desarrollado en el Liceo José Antonio Abreu del estado Trujillo.

> **Importante:** los contenidos de anatomía y fisiología se prepararon como materiales didácticos de apoyo. Los módulos de gestión antropométrica, informes y evaluaciones físicas constituyen una ampliación tecnológica de la investigación; no se afirma que formaran parte de la página web original.

## Inicio rápido en Windows

1. Descomprime el ZIP en una carpeta de tu computadora.
2. Instala **Python 3.10 o superior** desde [python.org](https://www.python.org/downloads/) si no lo tienes. Marca «Add Python to PATH» durante la instalación.
3. Ejecuta **`INICIAR_WINDOWS.bat`**.
4. La primera vez te pedirá **nombre, correo y contraseña** del administrador (mínimo 12 caracteres). No hay contraseña prefijada.
5. Con el servidor funcionando, entra desde el navegador a **http://127.0.0.1:8000**.
6. Selecciona **Acceso docente** e inicia sesión.
7. Si deseas detener el servidor, presiona `Ctrl+C` en la ventana de la terminal.

Si Windows no reconoce Python, instálalo y vuelve a abrir la terminal.

## Inicio rápido en Linux/macOS

```bash
cd Plataforma_Educacion_Fisica
python3 app.py init
python3 app.py
```

La segunda vez no necesitas repetir `init`.

También puedes iniciar manualmente en Windows:

```powershell
py -3 app.py init
py -3 app.py
```

**No hay que instalar paquetes** mediante `pip`.

## Qué puedes hacer

### Para docentes

- Iniciar sesión con contraseña segura.
- Crear años escolares, grados y secciones.
- Registrar, editar y activar/desactivar estudiantes.
- Guardar mediciones de peso, estatura, cintura, cadera, envergadura y frecuencia cardíaca.
- Calcular IMC automáticamente en cada registro.
- Visualizar historial de mediciones y gráficas de evolución.
- Registrar pruebas de velocidad, salto, flexibilidad, resistencia y equilibrio.
- Consultar estadísticas descriptivas individuales y cantidad de estudiantes por sección.
- Exportar registros antropométricos a CSV compatible con Excel.
- Usar un cronómetro de vueltas y un temporizador para actividades.
- Crear cuentas de docentes desde el administrador.

### Para estudiantes y visitantes

- Consultar contenidos de Educación Física, anatomía funcional, fisiología del ejercicio, capacidades físicas, hábitos saludables y tecnología educativa.
- Realizar retos de práctica con retroalimentación instantánea.
- Abrir retos mediante códigos QR (en la misma computadora o con acceso desde la red local).
- Usar calculadoras de IMC, relación cintura-cadera, frecuencia cardíaca y ritmo de carrera, sin guardar datos personales.

## Primeros pasos

1. Accede al panel como administrador.
2. En **Usuarios**, crea un docente (puedes utilizar inicialmente el propio administrador como docente).
3. En **Años y secciones**, crea un grupo. Por ejemplo: 2026-2027, 1.º, B.
4. En **Estudiantes**, crea registros (utiliza información ficticia para demostraciones).
5. Abre la ficha de un estudiante y selecciona **Añadir medición**.
6. Introduce peso y estatura: se mostrará una vista previa del IMC y el dato se guardará al confirmar.
7. Repite el registro en otra fecha para ver la evolución.
8. Registra una prueba física desde **Pruebas físicas**.
9. Consulta **Estadísticas** y **Informes**.

## Copias de seguridad

Detén la aplicación antes de hacer una copia. Guarda el archivo:

`datos/educacion_fisica.sqlite3`

Puedes copiar ese archivo a un medio seguro. Nunca subas la base de datos con registros reales a un repositorio público.

La carpeta `datos/` se crea automáticamente. El ZIP distribuido está **vacío de datos privados y contraseñas**.

## Uso de los códigos QR en celulares

Por defecto, el sistema escucha solo en `127.0.0.1`, es decir, solo en tu computadora, para reducir riesgos.

Para una demostración en la misma red local, puedes iniciar el servidor aceptando conexiones de tu Wi-Fi. Hazlo solo en una red de confianza y **con datos ficticios**, porque este servidor no incluye HTTPS:

En Windows PowerShell:

```powershell
$env:EF_HOST="0.0.0.0"
py -3 app.py
```

Después abre desde el teléfono la **IP local de la PC**, por ejemplo `http://192.168.1.20:8000` (sustituye por la dirección real). Los códigos QR mostrados bajo esa dirección enlazarán a la misma IP. Asegúrate de que el firewall permita el acceso si es necesario.

No expongas el servidor directamente a Internet.

## Privacidad y limitaciones

- La plataforma es un **MVP de uso local**, no está certificada para producción institucional.
- No recopila ni publica datos de estudiantes en la parte pública de la web.
- Un docente solo accede a estudiantes pertenecientes a sus propias secciones; el administrador puede gestionar los grupos.
- Las contraseñas se derivan usando PBKDF2-HMAC-SHA256 con sal aleatoria.
- Las sesiones de usuario utilizan cookies `HttpOnly` y `SameSite=Lax`, expiran automáticamente, y los formularios privados cuentan con CSRF.
- Se requiere autorización institucional y consentimiento aplicable antes de introducir datos reales de menores.
- El IMC en menores **no debe clasificarse con tablas de adultos**. Los cálculos son descriptivos, nunca diagnósticos.
- Los resultados de pruebas motrices no contienen baremos clínicos o clasificaciones automáticas.
- Para uso con datos reales en una red o en Internet se requiere despliegue con HTTPS, endurecimiento de seguridad, auditoría, copias de seguridad, permisos y política de conservación de datos.
- Esta versión no incorpora todavía editor de mediciones históricas, repositorio de archivos multimedia subidos por docentes ni evaluación clínica.

## Estructura del proyecto

```text
Plataforma_Educacion_Fisica/
├── app.py               # Servidor web y flujos de la aplicación
├── db.py                # Tablas, conexión y autenticación de SQLite
├── ui.py                # Componentes HTML reutilizables
├── content.py           # Lecciones y retos educativos
├── static/
│   ├── styles.css       # Estilos azul marino, azul celeste y blanco
│   ├── app.js           # Calculadoras, formularios y cronómetro
│   └── favicon.svg      # Icono EF+
├── qrcode/              # Biblioteca QR empaquetada localmente (BSD)
├── tests/
│   └── test_app.py      # Pruebas automatizadas
├── INICIAR_WINDOWS.bat
├── INICIAR_LINUX.sh
└── README.md
```

La carpeta `datos/` aparece después de inicializar el sistema.

## Despliegue en Dokploy y Hexper Ops (Docker)

La plataforma incluye un `Dockerfile` optimizado y reproducible configurado para producción en **Dokploy** y **Hexper Ops**:

- **Puerto:** Escucha en `0.0.0.0:8080` (declarado mediante `EXPOSE 8080`).
- **Seguridad:** Se ejecuta bajo un usuario sin privilegios (`appuser`).
- **Healthcheck:** Verificación integrada en `http://127.0.0.1:8080/`.
- **Base de datos:** Utiliza SQLite con almacenamiento persistente en `/app/datos`. En Hexper Ops / Dokploy selecciona *"la aplicación no necesita base de datos"* (y si deseas conservar los registros entre redespliegues, monta un volumen persistente en `/app/datos`).

### Variables de entorno recomendadas (en tiempo de ejecución)

Configura estas variables en el panel de Dokploy / Hexper Ops sin guardarlas en Git:

| Variable | Descripción | Ejemplo ficticio |
| :--- | :--- | :--- |
| `EF_ADMIN_EMAIL` | Correo del administrador inicial | `admin@ejemplo.edu` |
| `EF_ADMIN_PASSWORD` | Contraseña del administrador inicial (mínimo 12 caracteres) | `ClaveCompleja2026!` |
| `EF_ADMIN_NAME` | Nombre para la cuenta de administración | `Administrador General` |
| `EF_ENV` | Entorno de ejecución (`production`) | `production` |


## Pruebas

```bash
python -m unittest discover -s tests -v
```

Incluye pruebas de cálculos, seguridad de rutas, login, formularios, guardado en SQLite, acceso por docente, exportación CSV y códigos QR.

## Personalización

- Colores y diseño visual: `static/styles.css` (variables CSS al principio).
- Textos educativos y actividades: `content.py`.
- Estructura de datos: `db.py`.
- Páginas y navegación: `app.py` y `ui.py`.

## Licencia de terceros

El código QR se genera mediante `python-qrcode` (Copyright Lincoln Loop), distribuido bajo licencia BSD. Ver `qrcode/LICENSE-BSD.txt`.

---

**EF+ · Educación Física + Tecnología.** Primera versión funcional para desarrollo, demostración y ampliación progresiva con Codex.
