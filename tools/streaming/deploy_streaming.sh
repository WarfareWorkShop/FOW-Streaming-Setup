#!/usr/bin/env bash
set -euo pipefail

TARGET=""
HOST="localhost"

show_help() {
  cat <<USAGE
Uso: $0 --target <ruta> [--host <hostname>]

Copia los archivos de configuración de streaming a la ruta indicada. Si el host
proporcionado es distinto a 'localhost', se utilizará scp para la transferencia.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Opción desconocida: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "Debes indicar un directorio destino con --target" >&2
  exit 1
fi

copy_file() {
  local file="$1"
  local destination="$2"
  if [[ "$HOST" == "localhost" ]]; then
    mkdir -p "${TARGET}"
    cp "${file}" "${destination}"
  else
    scp "${file}" "${HOST}:${destination}"
  fi
}

copy_file "$(dirname "$0")/obs_profile.json" "${TARGET}/obs_profile.json"
copy_file "$(dirname "$0")/mist_server_config.yaml" "${TARGET}/mist_server_config.yaml"

cat <<INFO
Archivos desplegados en ${HOST}:${TARGET}

Para importar el perfil de OBS:
1. Abre OBS Studio.
2. Ve a Perfil -> Importar.
3. Selecciona ${TARGET}/obs_profile.json.

Para MistServer copia el archivo mist_server_config.yaml a /etc/mist/config.yaml
(y reinicia el servicio) o ajusta la ruta según tu instalación.
INFO
