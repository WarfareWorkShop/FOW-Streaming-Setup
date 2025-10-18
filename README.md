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
- **lanzadados*.md / .ino**: Documentación y prototipos de hardware para lectura de dados (no conectados al software).

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

### OpenAI

- `OPENAI_API_KEY`: clave de API (obligatoria para usar este proveedor).
- `OPENAI_MODEL`: modelo a utilizar (por defecto `gpt-3.5-turbo`).
- `OPENAI_BASE_URL`: URL base de la API (por defecto `https://api.openai.com/v1`).
- `OPENAI_TEMPERATURE`: temperatura para la generación (por defecto `0.7`).

### Anthropic

- `ANTHROPIC_API_KEY`: clave de API (obligatoria para usar este proveedor).
- `ANTHROPIC_MODEL`: modelo a utilizar (por defecto `claude-3-haiku-20240307`).
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
