# Bosch BME280 sensor
Temperature, humidity and pressure measurement using a Raspberry Pi Pico W with I2C on the Bosch BME280 and sending its data to an MQTT server.

## Cabling
- Pin 1 on `SDA`
- Pin 2 on `SCL`
- Pin 36 on `VIN`
- Pin 38 on `GND`

## Flashing
- Fill in the networkcredentials and MQTT server paths.
- both python files on the root folder of the Raspberry Pi Pico W
	- `bme280.py` and `main.py`
