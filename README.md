# Flames of War Streaming Setup

## Descripción

Este repositorio recoge los distintos experimentos y prototipos necesarios para construir un sistema de streaming para partidas
 de Flames of War. El código incluido actualmente cubre únicamente funcionalidades básicas y sirve como punto de partida para
 iteraciones futuras.

## Estructura del proyecto

- **backend/**: Aplicación Flask con registro, inicio de sesión y un endpoint de chat que devuelve una respuesta simulada.
- **frontend/src/App.js**: Interfaz React mínima para enviar mensajes de texto al backend.
- **frontend/src/VoiceInteraction.js**: Ejemplo de transcripción de voz en el navegador (no integrado con el backend).
- **frontend/imageprocessing.py**: Script independiente con utilidades de OpenCV para analizar imágenes estáticas.
- **lanzadados*.md / .ino**: Documentación y prototipos de hardware para lectura de dados (no conectados al software).

## Estado actual de las funcionalidades

### Implementado

- Registro e inicio de sesión con almacenamiento en SQLite y emisión de JWT.
- Endpoint `/api/chat` que devuelve una respuesta placeholder para probar la comunicación frontend-backend.
- Interfaz React para enviar mensajes al endpoint de chat y visualizar la respuesta simulada.
- Ejemplo de reconocimiento de voz en el navegador mediante `webkitSpeechRecognition`.
- Script de procesamiento de imágenes con OpenCV que detecta contornos y genera una imagen de salida.

### TODO / Próximos pasos

- **Integración real con OpenAI**: consumir la API para generar respuestas y gestionar claves de forma segura.
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

## Puesta en marcha

### Backend

```bash
cd backend
pip install -r requirements.txt
flask --app app run
```

> **TODO**: configurar variables de entorno para `SECRET_KEY`, `DATABASE_URI` y la clave de OpenAI cuando se implemente la integración real.

### Frontend

```bash
cd frontend
npm install
npm start
```

> **TODO**: consolidar la aplicación React (integrar voz, manejo de partidas y visualización del estado del juego).

## Contribuir

¡Las contribuciones son bienvenidas! Abre un issue para discutir nuevas ideas o envía un pull request con mejoras concretas.

## Licencia

Este proyecto está licenciado bajo la licencia BSD-3-Clause. Consulta el archivo `LICENSE` para más detalles.
