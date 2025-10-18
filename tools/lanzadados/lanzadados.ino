#include <Servo.h>

Servo myservo;

// Pines
const int servoPin = 9;
const int potSpeed = A0; // Potenciómetro para ajustar la velocidad
const int potAngle = A1; // Potenciómetro para ajustar el ángulo

// Variables
int angle = 90;  // Ángulo inicial de lanzamiento
int speed = 100; // Velocidad inicial de lanzamiento (en milisegundos)

void setup() {
  myservo.attach(servoPin);
  myservo.write(0); // Posición inicial
  Serial.begin(9600); // Inicializa la comunicación serial
}

void loop() {
  speed = map(analogRead(potSpeed), 0, 1023, 50, 500); // Lee el potenciómetro de velocidad
  angle = map(analogRead(potAngle), 0, 1023, 30, 150); // Lee el potenciómetro de ángulo

  // Muestra los valores en el monitor serial
  Serial.print("Velocidad: ");
  Serial.print(speed);
  Serial.print(" ms, Ángulo: ");
  Serial.print(angle);
  Serial.println(" grados");

  if (Serial.available()) {
    char command = Serial.read();
    if (command == 'l') {
      launchDice(angle, speed);
    } else if (command == 'r') {
      resetServo();
    }
  }
}

void launchDice(int angle, int speed) {
  myservo.write(angle); // Mueve el servomotor al ángulo de lanzamiento
  delay(speed);         // Espera el tiempo especificado para la velocidad
  myservo.write(0);     // Vuelve a la posición inicial
}

void resetServo() {
  myservo.write(0); // Vuelve a la posición inicial
}
