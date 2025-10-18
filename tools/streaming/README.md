# Streaming automation

Este directorio contiene una configuración de referencia para OBS Studio y MistServer
utilizada durante las pruebas internas del proyecto. Los archivos permiten reproducir
un entorno de streaming básico con superposiciones informativas generadas a partir
de los datos de las partidas gestionadas por el backend.

## Contenido

- `obs_profile.json`: Perfil de OBS con escenas preconfiguradas, fuentes de audio y
  superposiciones para mostrar el estado de la partida.
- `mist_server_config.yaml`: Configuración de MistServer con los puntos de montaje y
  parámetros de retransmisión utilizados en el laboratorio.
- `deploy_streaming.sh`: Script para instalar los archivos en un servidor remoto o en
  un entorno local de pruebas.

## Uso rápido

```bash
./deploy_streaming.sh --target /opt/fow-streaming --host obs.example.com
```

El script creará el directorio indicado, copiará los archivos de configuración y
mostrará instrucciones para importar el perfil en OBS Studio.
