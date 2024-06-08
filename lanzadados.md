# Lanzador de Dados con Arduino

Este proyecto es un programa para Arduino que controla un servomotor para lanzar dados en juegos de mesa. El programa permite ajustar la velocidad y el ángulo de lanzamiento mediante potenciómetros, lo que brinda una experiencia de juego más emocionante y personalizada.

## Requisitos

- Arduino UNO o compatible
- Servomotor
- 2 Potenciómetros
- Cables de conexión
- IDE de Arduino

## Instalación

1. Descarga el archivo `lanzadados.ino` de este repositorio.
2. Abre el IDE de Arduino.
3. Ve a `Archivo` > `Abrir` y selecciona el archivo `lanzadados.ino`.
4. Verifica que la placa y el puerto serial estén configurados correctamente en el IDE.
5. Carga el programa en tu placa Arduino.

## Conexiones

- Conecta el servomotor al pin 9 de tu Arduino.
- Conecta un potenciómetro al pin analógico A0 para controlar la velocidad de lanzamiento.
- Conecta el otro potenciómetro al pin analógico A1 para controlar el ángulo de lanzamiento.
- Asegúrate de conectar los potenciómetros a tierra (GND) y a la alimentación de 5V.

## Uso

1. Abre el monitor serial en el IDE de Arduino y establece la velocidad en baudios a 9600.
2. Gira los potenciómetros para ajustar el ángulo y la velocidad de lanzamiento. Los valores se mostrarán en el monitor serial.
3. Escribe 'l' (sin comillas) y presiona Enter para lanzar los dados con los valores actuales de ángulo y velocidad.
4. Escribe 'r' (sin comillas) y presiona Enter para resetear el servomotor a la posición inicial.

## Funciones principales

- `setup()`: Inicializa el servomotor y la comunicación serial.
- `loop()`: Lee los valores de los potenciómetros, muestra los valores en el monitor serial y verifica si hay comandos enviados por el usuario.
- `launchDice(angle, speed)`: Mueve el servomotor al ángulo especificado, espera el tiempo especificado para la velocidad, y luego vuelve a la posición inicial.
- `resetServo()`: Mueve el servomotor a la posición inicial (0 grados).

## Contribuciones

Si tienes alguna sugerencia o mejora, no dudes en abrir un issue o enviar un pull request.

## Licencia

Este proyecto está licenciado bajo la licencia BSD-3-Clause. Consulta el archivo [LICENSE](LICENSE) para más detalles.
