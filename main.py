# import modules
import network
import socket
import time
from machine import Pin, I2C
from umqtt.simple import MQTTClient
import bme280

# LED configuration
led = Pin("LED", Pin.OUT)

# Wi-Fi configuration
wifi_ssid = "<SSID>"
wifi_password = "<PASSWD>"

# MQTT broker configuration
mqtt_broker = "<MQTT_BROKER_IP>"
mqtt_port = 1883
mqtt_username = "<MQTT_BROKER_USERNAME>"
mqtt_password = "<MQTT_BROKER_PASSWD>"
mqtt_temperature_topic = "<TOPIC_DIRECTORY>/temperature"
mqtt_pressure_topic = "<TOPIC_DIRECTORY>/pressure"
mqtt_humidity_topic = "<TOPIC_DIRECTORY>/humidity"

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
    wlan.connect(wifi_ssid, wifi_password)
    while not wlan.isconnected():
        time.sleep(30)
    print("Connected to Wi-Fi:", wlan.ifconfig())


def connect_mqtt():
    client.connect()
    print("Connected to MQTT broker")


def publish_data(topic, data, retain=True):
    client.publish(topic, data, retain=retain)
    print("Published data to {}: {}".format(topic, data))


def read_sensor():
    temperature, pressure, humidity = bme.read_compensated_data()
    return temperature / 100, round(pressure / 25600, 2), round(humidity / 1024, 2)


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
