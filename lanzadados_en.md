# Dice Launcher with Arduino

This project is an Arduino program that controls a servo motor to launch dice in board games. The program allows you to adjust the launch speed and angle using potentiometers, providing a more exciting and personalized gaming experience.

## Requirements

- Arduino UNO or compatible
- Servo motor
- 2 Potentiometers
- Connection cables
- Arduino IDE

## Installation

1. Download the `launched.ino` file from this repository.
2. Open the Arduino IDE.
3. Go to `File` > `Open` and select the `launched.ino` file.
4. Check that the board and serial port are configured correctly in the IDE.
5. Upload the program to your Arduino board.

## Connections

- Connect the servo motor to pin 9 of your Arduino.
- Connect a potentiometer to analog pin A0 to control the launch speed.
- Connect the other potentiometer to analog pin A1 to control the launch angle.
- Make sure to connect the potentiometers to GND and 5V power.

## Usage

1. Open the serial monitor in the Arduino IDE and set the baud rate to 9600.
2. Turn the potentiometers to adjust the launch angle and speed. The values ​​will be displayed on the serial monitor.
3. Type 'l' (without quotes) and press Enter to roll the dice with the current angle and speed values.
4. Type 'r' (without quotes) and press Enter to reset the servo motor to the initial position.

## Main functions

- `setup()`: Initializes the servo motor and serial communication.
- `loop()`: Reads the values ​​from the potentiometers, displays the values ​​on the serial monitor, and checks for any commands sent by the user.
- `launchDice(angle, speed)`: Moves the servo to the specified angle, waits for the specified speed time, and then returns to the home position.
- `resetServo()`: Moves the servo to the home position (0 degrees).

## Contributions

If you have any suggestions or improvements, feel free to open an issue or send a pull request.

## License

This project is licensed under the BSD-3-Clause license. See the [LICENSE](LICENSE) file for more details.
