# import modules
import network
import socket
import time
from machine import Pin, I2C
from umqtt.simple import MQTTClient
import bme280
import json

# LED configuration
led = Pin("LED", Pin.OUT)


# Load configuration from file
def load_config():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config
    except Exception as e:
        print("Failed to load configuration:", e)
        return None


# Load configuration
config = load_config()
if not config:
    print("Exiting due to configuration error.")
    raise SystemExit

# Wi-Fi configuration
wifi_ssid = config["wifi"]["ssid"]
wifi_password = config["wifi"]["password"]

# MQTT broker configuration
mqtt_broker = config["mqtt"]["broker"]
mqtt_port = config["mqtt"]["port"]
mqtt_username = config["mqtt"]["username"]
mqtt_password = config["mqtt"]["password"]
mqtt_client_id = config["mqtt"]["client_id"]
mqtt_temperature_topic = config["mqtt"]["topics"]["temperature"]
mqtt_pressure_topic = config["mqtt"]["topics"]["pressure"]
mqtt_humidity_topic = config["mqtt"]["topics"]["humidity"]


# BME280 sensor configuration
i2c = I2C(id=0, scl=Pin(1), sda=Pin(0), freq=100000)
bme = bme280.BME280(i2c=i2c)

# MQTT client configuration
client_id = "<MQTT_CLIENT_ID>"
client = MQTTClient(
    client_id, mqtt_broker, mqtt_port, mqtt_username, mqtt_password, keepalive=650
)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    while not wlan.isconnected():
        try:
            print("Connecting to Wi-Fi...")
            wlan.connect(wifi_ssid, wifi_password)
            time.sleep(10)  # Wait for 10 seconds before checking connection status
        except Exception as e:
            print("Wi-Fi connection failed:", e)
            blink_led(0.1, 10)  # Rapid blinking to indicate Wi-Fi error
            time.sleep(30)  # Wait for 30 seconds before retrying
    print("Connected to Wi-Fi:", wlan.ifconfig())


def connect_mqtt():
    while True:
        try:
            client.connect()
            print("Connected to MQTT broker")
            break
        except Exception as e:
            print("MQTT connection failed:", e)
            blink_led(0.5, 5)  # Slow blinking to indicate MQTT error
            time.sleep(30)  # Wait for 30 seconds before retrying


def publish_data(topic, data, retain=True):
    try:
        client.publish(topic, data, retain=retain)
        print("Published data to {}: {}".format(topic, data))
    except Exception as e:
        print("Failed to publish data:", e)
        blink_led(0.5, 5)  # Slow blinking to indicate MQTT publish error
        connect_mqtt()  # Reconnect to MQTT broker


def read_sensor():
    try:
        temperature, pressure, humidity = bme.read_compensated_data()
        return temperature / 100, round(pressure / 25600, 2), round(humidity / 1024, 2)
    except Exception as e:
        print("Failed to read sensor data:", e)
        blink_led(0.2, 20)  # Fast blinking to indicate sensor error
        return None, None, None


def blink_led(interval, count):
    for _ in range(count):
        led.on()
        time.sleep(interval)
        led.off()
        time.sleep(interval)


def main():
    connect_wifi()
    connect_mqtt()

    while True:
        temperature, pressure, humidity = read_sensor()
        publish_data(mqtt_temperature_topic, str(temperature))
        publish_data(mqtt_pressure_topic, str(pressure))
        publish_data(mqtt_humidity_topic, str(humidity))
        for _ in range(300):  # 600 one-second intervals for sign of life
            led.on()
            time.sleep(1)
            led.off()
            time.sleep(1)


if __name__ == "__main__":
    main()
