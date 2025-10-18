# Flames of War Streaming Setup

## Descripción

Este repositorio recoge los distintos experimentos y prototipos necesarios para construir un sistema de streaming para partidas
de Flames of War. El código incluido actualmente cubre funcionalidades básicas y sirve como punto de partida para iteraciones
futuras.

## Estructura del proyecto

- **backend/**: Aplicación Flask con registro, inicio de sesión y un endpoint de chat con integración con OpenAI, Anthropic y un
  modelo local compatible con LM Studio.
- **frontend/src/App.js**: Interfaz React mínima para enviar mensajes de texto al backend.
- **frontend/src/VoiceInteraction.js**: Ejemplo de transcripción de voz en el navegador (no integrado con el backend).
- **frontend/imageprocessing.py**: Script independiente con utilidades de OpenCV para analizar imágenes estáticas.
- **tools/lanzadados/***: Documentación y prototipos de hardware para lectura de dados (no conectados al software).

## Estado actual de las funcionalidades

### Implementado

- Registro e inicio de sesión con almacenamiento en SQLite y emisión de JWT.
- Endpoint `/api/chat` capaz de delegar en OpenAI, Anthropic o un endpoint local de LM Studio en función de la configuración.
- Interfaz React para enviar mensajes al endpoint de chat y visualizar las respuestas.
- Ejemplo de reconocimiento de voz en el navegador mediante `webkitSpeechRecognition`.
- Script de procesamiento de imágenes con OpenCV que detecta contornos y genera una imagen de salida.

### TODO / Próximos pasos

- **IA como oponente**: definir lógica de juego, almacenamiento de estado y comunicación de turnos.
- **Procesamiento de imagen en tiempo real**: integrar `imageprocessing.py` con el backend para automatizar la lectura de dados.
- **Interacción por voz end-to-end**: conectar `VoiceInteraction.js` con la API y habilitar respuestas habladas.
- **Configuración y automatización de streaming**: documentar perfiles reales de OBS/Mist Server y proveer scripts de despliegue.
- **Gestión avanzada de usuarios y partidas**: roles, invitaciones, emparejamiento y persistencia de sesiones.
- **Pruebas automatizadas**: añadir suites de tests para backend y frontend, así como pipelines de CI/CD.

## Requisitos

- Python 3.10+
- Node.js 18+
- SQLite (incluido con Python) o una base de datos compatible con SQLAlchemy.
- Dependencias de Python listadas en `backend/requirements.txt` (crea un entorno virtual y ejecuta `pip install -r requirements.txt`).

## Configuración de la IA

El backend puede conectarse a tres proveedores distintos. Configura las variables de entorno antes de iniciar Flask:

- `DEFAULT_AI_PROVIDER`: `openai`, `anthropic` o `lmstudio` (por defecto `openai`).
- `AI_REQUEST_TIMEOUT`: tiempo máximo en segundos para esperar la respuesta (por defecto `30`).

### Endpoints de Autenticación

El backend expone un conjunto de endpoints JSON para la gestión de usuarios y sesiones. Todos devuelven respuestas en formato `application/json`.

#### `POST /register`

- **Payload**

  ```json
  {
    "username": "usuario",
    "password": "contraseña"
  }
  ```

- **Respuestas**
  - `201 Created`: registro exitoso.
    ```json
    {"message": "User registered successfully!"}
    ```
  - `400 Bad Request`: falta `username`/`password`, son inválidos o están vacíos.
    ```json
    {"message": "Username and password are required."}
    ```
    ```json
    {"message": "Username and password cannot be empty."}
    ```
  - `409 Conflict`: el nombre de usuario ya existe.
    ```json
    {"message": "Username is already taken."}
    ```
  - `500 Internal Server Error`: error al crear el usuario.
    ```json
    {"message": "Could not register user. Please try again later."}
    ```

#### `POST /login`

- **Payload**

  ```json
  {
    "username": "usuario",
    "password": "contraseña"
  }
  ```

- **Respuestas**
  - `200 OK`: credenciales válidas, devuelve token JWT.
    ```json
    {"token": "<jwt>"}
    ```
  - `400 Bad Request`: falta `username`/`password`, son inválidos o están vacíos.
    ```json
    {"message": "Username and password are required."}
    ```
    ```json
    {"message": "Username and password cannot be empty."}
    ```
  - `401 Unauthorized`: credenciales inválidas.
    ```json
    {"message": "Invalid credentials!"}
    ```

#### `GET /me`

- **Headers**
  - `Authorization: Bearer <jwt>`

- **Respuestas**
  - `200 OK`: devuelve la información del usuario autenticado.
    ```json
    {
      "id": 1,
      "username": "usuario"
    }
    ```
  - `401 Unauthorized`: token ausente o inválido (gestionado por JWT).
  - `404 Not Found`: el usuario referenciado por el token no existe.

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

### Launcher interactivo

Para simplificar los primeros pasos puedes utilizar el script `launcher.py` situado
en la raíz del repositorio. Solo necesitas tener Python 3.10+ instalado:

```bash
python launcher.py
```

El lanzador mostrará un menú en castellano desde el que podrás:

- Instalar las dependencias del backend (`pip install -r backend/requirements.txt`).
- Instalar las dependencias del frontend (`npm install`).
- Ejecutar el servidor de Flask del backend.
- Ejecutar el servidor de desarrollo de React.
- Consultar un resumen rápido del entorno y las herramientas detectadas.

Cada opción explica cómo detener el proceso (normalmente con `Ctrl+C`) para
volver al menú principal.

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
