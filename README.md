# Flames of War Streaming Setup

## Descripción

Este repositorio recoge los distintos experimentos y prototipos necesarios para construir un sistema de streaming para partidas
de Flames of War. El código incluido actualmente cubre funcionalidades básicas y sirve como punto de partida para iteraciones
futuras.

## Estructura del proyecto

- **backend/**: Aplicación Flask con autenticación reforzada, límites de velocidad y endpoints tácticos específicos para Flames of War.
- **frontend/src/App.js**: Centro táctico React con gestión de sesión, chat, analizador de listas, entrenador virtual y bitácora de turnos.
- **frontend/src/VoiceInteraction.js**: Componente de reconocimiento de voz integrado con el flujo de registro de turnos y chat.
- **frontend/imageprocessing.py**: Script independiente con utilidades de OpenCV para analizar imágenes estáticas.
- **tools/lanzadados/***: Documentación y prototipos de hardware para lectura de dados (no conectados al software).

## Estado actual de las funcionalidades

### Implementado

- Autenticación con JWT de acceso y refresco, revocación por lista negra y protección frente a ataques de fuerza bruta.
- Endpoint `/api/chat` autenticado, con validaciones de contenido, listas de bloqueo y límites de velocidad configurables.
- Circuito táctico con endpoints para análisis de escenario, evaluación de listas y coaching contextual.
- Bitácora persistente de turnos para crear una biblioteca de replays y analizar decisiones posteriores a la partida.
- Interfaz React con login completo, panel táctico, reconocimiento de voz integrado y accesos directos a herramientas externas de Flames of War.
- Scripts de Flask-Migrate y documentación para mantener el esquema de base de datos actualizado.
- Pruebas automatizadas para la lógica principal del backend y del frontend.

## Requisitos

- Python 3.10+
- Node.js 18+
- SQLite (incluido con Python) o una base de datos compatible con SQLAlchemy.
- Dependencias de Python listadas en `backend/requirements.txt` (crea un entorno virtual y ejecuta `pip install -r requirements.txt`).

## Configuración de la IA

El backend puede conectarse a tres proveedores distintos. Configura las variables de entorno antes de iniciar Flask:

- `DEFAULT_AI_PROVIDER`: `openai`, `anthropic` o `lmstudio` (por defecto `openai`).
- `AI_REQUEST_TIMEOUT`: tiempo máximo en segundos para esperar la respuesta (por defecto `30`).

### Endpoints de Autenticación y gestión de sesión

El backend expone endpoints JSON para la gestión de usuarios. Las respuestas utilizan el campo `message` para describir errores.

| Método & Ruta             | Descripción                                                                 | Notas de seguridad                              |
| ------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------- |
| `POST /api/auth/register` | Registra un nuevo usuario aplicando políticas de contraseña y (opcional) CAPTCHA. | Configura `RECAPTCHA_SECRET_KEY` para activarlo. |
| `POST /api/auth/login`    | Devuelve `accessToken`, `refreshToken` y `expiresIn` cuando las credenciales son válidas. | Bloquea intentos fallidos repetidos.            |
| `POST /api/auth/refresh`  | Emite un nuevo token de acceso a partir del token de refresco.              | Envía el refresh token en la cabecera `Authorization`. |
| `POST /api/auth/logout`   | Revoca el token actual añadiéndolo a la lista negra.                        | Recomendado al cerrar sesión en clientes web.   |
| `GET /api/auth/me`        | Devuelve `id`, `username` y `email` del usuario autenticado.                | Requiere token de acceso vigente.               |

Los tokens se emiten con expiraciones configurables (`JWT_ACCESS_TOKEN_MINUTES`, `JWT_REFRESH_TOKEN_DAYS`). Cada cambio de contraseña revoca automáticamente los tokens emitidos con anterioridad.

### Endpoints tácticos para Flames of War

Todos los endpoints bajo `/api/tactics` requieren autenticación y respetan el límite definido en `TACTICS_RATE_LIMIT` (por defecto `20/minute`).

| Método & Ruta                       | Propósito                                                                                                   |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `POST /api/tactics/scenario-advice` | Genera recomendaciones basadas en el estado estructurado de la batalla (turno, unidades, clima, terreno...). |
| `POST /api/tactics/army-list`       | Evalúa la sinergia de una lista de ejército y sugiere mejoras de composición.                               |
| `POST /api/tactics/coach`           | Activa un modo de coaching con un rol táctico específico y devuelve prioridades y advertencias personalizadas. |
| `POST /api/tactics/logs`            | Guarda una bitácora de turno con entradas provenientes del chat o de la voz.                                |
| `GET /api/tactics/logs`             | Recupera las bitácoras más recientes del usuario autenticado.                                               |
| `DELETE /api/tactics/logs/<log_id>` | Elimina una bitácora previa del usuario.                                                                    |

### Configuración de la base de datos

El backend utiliza SQLite por defecto y crea un archivo `site.db` en el directorio `backend`. Puedes empezar con esta configuración sin realizar ningún cambio adicional. Para utilizar una base de datos distinta (por ejemplo, PostgreSQL o MySQL), establece la variable de entorno `DATABASE_URI` antes de iniciar la aplicación. Ejemplos:

- PostgreSQL: `export DATABASE_URI=postgresql+psycopg2://usuario:password@localhost:5432/fow`
- MySQL/MariaDB: `export DATABASE_URI=mysql+pymysql://usuario:password@localhost:3306/fow`

También puedes definir `SECRET_KEY` y `JWT_SECRET_KEY` si deseas claves distintas a las predeterminadas.

### Migraciones de base de datos

El proyecto integra [Flask-Migrate](https://flask-migrate.readthedocs.io/) para administrar la evolución del esquema. Dentro del directorio `backend` encontrarás scripts que simplifican los comandos habituales:

- `scripts/db_init.sh`: inicializa el directorio de migraciones (solo la primera vez).
- `scripts/db_migrate.sh "Mensaje"`: genera una nueva migración con el mensaje indicado.
- `scripts/db_upgrade.sh`: aplica las migraciones pendientes sobre la base de datos configurada.

Todos los scripts asumen que se ejecutan desde cualquier ubicación y configuran automáticamente `FLASK_APP=app:create_app`.

### Datos de prueba e inicialización automática

Para crear usuarios de ejemplo y automatizar la inicialización del entorno ejecuta:

```
cd backend
scripts/bootstrap.sh
```

El script `bootstrap.sh` aplica las migraciones y ejecuta `scripts/seed_users.py`, que crea usuarios de prueba (`test_user` y `streamer`) siempre que no existan. Si necesitas crear un usuario adicional durante el sembrado, define las variables `FIXTURE_CREATE_USER`, `FIXTURE_CREATE_EMAIL` y opcionalmente `FIXTURE_CREATE_PASSWORD` antes de ejecutar el script.

## Configurar el Frontend
- `OPENAI_API_KEY`: clave de API (obligatoria para usar este proveedor).
- `OPENAI_MODEL`: modelo a utilizar (por defecto `gpt-4o`).
- `OPENAI_BASE_URL`: URL base de la API (por defecto `https://api.openai.com/v1`).
- `OPENAI_TEMPERATURE`: temperatura para la generación (por defecto `0.7`).

### Anthropic

- `ANTHROPIC_API_KEY`: clave de API (obligatoria para usar este proveedor).
- `ANTHROPIC_MODEL`: modelo a utilizar (por defecto `claude-3.7-Sonnet`).
- `ANTHROPIC_BASE_URL`: URL base de la API (por defecto `https://api.anthropic.com`).
- `ANTHROPIC_API_VERSION`: versión de la API (por defecto `2023-06-01`).
- `ANTHROPIC_MAX_TOKENS`: tokens máximos por respuesta (por defecto `1024`).
- `ANTHROPIC_TEMPERATURE`: temperatura para la generación (por defecto `0.7`).

### LM Studio

- `LM_STUDIO_BASE_URL`: URL base del servidor local (por defecto `http://localhost:1234/v1`).
- `LM_STUDIO_MODEL`: nombre del modelo expuesto por LM Studio (obligatorio para obtener respuestas útiles).

## Puesta en marcha

### Backend

```bash
cd backend
pip install -r requirements.txt
flask --app app run
```

Asegúrate de exportar previamente las variables de entorno descritas en la sección anterior.

### Frontend

```bash
cd frontend
npm install
npm start
```

## Contribuir

¡Las contribuciones son bienvenidas! Abre un issue para discutir nuevas ideas o envía un pull request con mejoras concretas.

## Licencia

Este proyecto está licenciado bajo la licencia BSD-3-Clause. Consulta el archivo `LICENSE` para más detalles.
