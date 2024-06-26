# Flames of War Streaming Setup

## Descripción

Este proyecto proporciona una configuración completa para transmitir partidas de Flames of War utilizando OBS Studio, cámaras de video y Mist Server. Además de las funcionalidades básicas de streaming, hemos añadido una emocionante nueva característica que permite a los jugadores enfrentar a una Inteligencia Artificial (IA) como oponente. Esta IA utiliza ChatGPT de OpenAI para interactuar con los jugadores, procesar imágenes y videos en tiempo real para analizar el estado del juego, y reconocer resultados de tiradas de dados.

## Funcionalidades Principales

- Streaming de Video: Configuración detallada para transmitir partidas utilizando OBS Studio y Mist Server.
- Interacción por Voz: Integración con la Web Speech API para comandos de voz y respuestas de la IA en tiempo real.
- IA como Oponente: Uso de ChatGPT para jugar contra una IA en partidas de Flames of War.
- Procesamiento de Imágenes y Dados: Análisis de imágenes y videos para determinar el estado del juego y los resultados de las tiradas de dados.

## Configuración Inicial

### Requisitos

- OBS Studio
- VLC Media Player o Webcamoid
- Cámara USB
- Micrófono (opcional)
- Mist Server
- Python y bibliotecas como OpenCV para el procesamiento de imágenes
- API de OpenAI para ChatGPT

### Instalación

Dependiendo de tus preferencias, elige entre estos programas para stream. Serán los que recojan la imagen de las cámaras (los ojos de la IA).

1. **OBS Studio:**
   - Descarga e instala OBS Studio desde [OBS Studio](https://obsproject.com/).
2. **VLC Media Player:**
   - Descarga e instala VLC desde [VLC Media Player](https://www.videolan.org/vlc/).
3. **Webcamoid:**
   - Descarga e instala Webcamoid desde [Webcamoid](https://webcamoid.github.io/).
4. **Mist Server:**
   - Descarga e instala Mist Server desde [Mist Server](https://mistserver.org/).

## Clonar el Repositorio

`      git clone https://github.com/WarfareWorkShop/FOW-Streaming-Setup.git
      cd FOW-Streaming-Setup`

## Configurar el Backend

- Instala las dependencias:

  `cd backend
  pip install -r requirements.txt`
- Configura las variables de entorno para la API de OpenAI y la base de datos.

## Configurar el Frontend

- Instala las dependencias:

  `cd frontend npm install`
- Inicia el servidor de desarrollo:

  `npm start`
- Configurar el Servidor de Streaming de Video

## Iniciar la IA como Oponente

En el backend, inicia el servidor Flask para manejar las solicitudes de la API:

`      cd backend
      flask run`

- Configura y prueba la interacción con ChatGPT desde el frontend para recibir y enviar mensajes a la IA.

## Interacción por Voz

Usa la interfaz de usuario para enviar comandos de voz a la IA y recibir respuestas habladas en tiempo real.
Procesamiento de Imágenes y Dados

Sube imágenes o videos del tablero de juego y deja que la IA analice el estado actual y los resultados de los dados.

### Configuración de OBS

1. **Importar Perfiles y Escenas:**
   - Exporta tu perfil y configuración de escena desde OBS y súbelos al repositorio.
   - En OBS, ve a "Perfil" > "Importar" y selecciona el archivo exportado.
   - Repite el proceso para las escenas.
2. **Agregar Fuentes:**
   - Añade tus cámaras y ajusta sus posiciones en la ventana de vista previa de OBS.
3. **Integrar Mist Server:**
   - Configura Mist Server para que pueda ser utilizado como fuente en OBS.
   - Agrega Mist Server como fuente en OBS y configura sus ajustes según sea necesario.

### Ejemplo de configuración

- **PC 1:**
  - 2 cámaras USB 2K conectadas
  - Una cámara enfocada en el tablero completo
  - Otra cámara enfocada en los dados
  - Instala y configura Mist Server en este PC
    - Abre Mist Server y crea una nueva "Fuente de Captura"
    - Selecciona las cámaras USB como dispositivos de captura
    - Configura la resolución y tasa de frames deseada
    - Habilita la opción "Transmitir esta fuente"
    - Anota la dirección IP y puerto que Mist Server está utilizando para transmitir
  - Transmite los videos a través de la LAN usando Mist Server
- **PC 2:**
  - Instala OBS Studio en este PC
  - En OBS, crea una nueva escena
  - Añade una "Fuente de Medios" para cada cámara
    - Selecciona "Mist Fuente de Red" como tipo de fuente
    - Ingresa la dirección IP y puerto del PC 1 que está transmitiendo con Mist Server
  - Posiciona y ajusta las fuentes de cámara en la escena de OBS
  - Configura el audio (micrófono, etc.) según sea necesario
  - Configura la salida de streaming hacia la plataforma deseada (YouTube, Twitch, etc.)
  - Recibe los videos transmitidos por la LAN desde PC 1
  - Transmite hacia plataformas de internet (YouTube, Twitch, etc.) utilizando OBS Studio

### Uso

1. **Iniciar Streaming:**
   - En el PC 1, inicia la transmisión en Mist Server
   - En el PC 2, configura tu clave de transmisión en OBS para la plataforma de tu elección (YouTube, Twitch)
   - En el PC 2, haz clic en "Start Streaming" en OBS para comenzar a transmitir
2. **Monitorear el Stream:**
   - Usa un dispositivo secundario para verificar la calidad del video y audio en la plataforma de streaming

## Contribuir

Si tienes mejoras, sugerencias o encuentras errores, por favor abre un issue o envía un pull request.

## Licencia

Este proyecto está licenciado bajo la licencia BSD-3-Clause. Consulta el archivo `LICENSE` para más detalles.
