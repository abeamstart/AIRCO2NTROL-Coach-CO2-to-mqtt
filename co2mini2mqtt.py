#!/usr/bin/env python3
import usb.core
import usb.util
import time
import paho.mqtt.client as mqtt
import json

# MQTT-Konfiguration
MQTT_BROKER = '192.168.1.254'  # Ersetze mit der IP-Adresse deines MQTT-Brokers
MQTT_PORT = 1883
MQTT_CLIENT_ID = 'co2pi1'
MQTT_USERNAME = 'mqtt'
MQTT_PASSWORD = 'meinpass4mqtt#Nairolf'

# Auto-Discovery Topics für Home Assistant
DISCOVERY_TOPIC_CO2 = 'homeassistant/sensor/co2pi1/co2/config'
DISCOVERY_TOPIC_TEMPERATURE = 'homeassistant/sensor/co2pi1/temperature/config'
DISCOVERY_TOPIC_HUMIDITY = 'homeassistant/sensor/co2pi1/humidity/config'

# Daten Topic
DATA_TOPIC = 'homeassistant/co2pi1/data'

# Warten, bis das CO2-Mini-Gerät verfügbar ist
while True:
    dev = usb.core.find(idVendor=0x04d9, idProduct=0xa052)
    if dev:
        break
    print("CO2-Mini-Gerät nicht gefunden, warte 5 Sekunden...")
    time.sleep(5)

# Schnittstelle beanspruchen
interface = 0
if dev.is_kernel_driver_active(interface):
    dev.detach_kernel_driver(interface)
usb.util.claim_interface(dev, interface)

# Initialisierungssequenz senden
init_sequence = b'\x00\x00\x00\x00\x00\x00\x00\x00'
dev.ctrl_transfer(0x21, 0x09, 0x0300, 0, init_sequence)

# MQTT-Client einrichten
client = mqtt.Client(MQTT_CLIENT_ID)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

# Home Assistant Auto-Discovery konfigurieren
def configure_home_assistant():
    payload_co2 = {
        "name": "CO2 Sensor Pi1",
        "state_topic": DATA_TOPIC,
        "value_template": "{{ value_json.co2 }}",
        "unit_of_measurement": "ppm",
        "device_class": "carbon_dioxide",
        "unique_id": "co2_sensor_co2pi1",
        "device": {
            "identifiers": ["co2pi1"],
            "name": "CO2 Sensor Pi1",
            "model": "CO2 Mini",
            "manufacturer": "Holtek"
        }
    }
    client.publish(DISCOVERY_TOPIC_CO2, json.dumps(payload_co2), retain=True)

    payload_temperature = {
        "name": "Temperature Sensor Pi1",
        "state_topic": DATA_TOPIC,
        "value_template": "{{ value_json.temperature }}",
        "unit_of_measurement": "°C",
        "device_class": "temperature",
        "unique_id": "temperature_sensor_co2pi1",
        "device": {
            "identifiers": ["co2pi1"],
            "name": "CO2 Sensor Pi1",
            "model": "CO2 Mini",
            "manufacturer": "Holtek"
        }
    }
    client.publish(DISCOVERY_TOPIC_TEMPERATURE, json.dumps(payload_temperature), retain=True)

    payload_humidity = {
        "name": "Humidity Sensor Pi1",
        "state_topic": DATA_TOPIC,
        "value_template": "{{ value_json.humidity }}",
        "unit_of_measurement": "%",
        "device_class": "humidity",
        "unique_id": "humidity_sensor_co2pi1",
        "device": {
            "identifiers": ["co2pi1"],
            "name": "CO2 Sensor Pi1",
            "model": "CO2 Mini",
            "manufacturer": "Holtek"
        }
    }
    client.publish(DISCOVERY_TOPIC_HUMIDITY, json.dumps(payload_humidity), retain=True)

# Home Assistant Discovery konfigurieren
configure_home_assistant()

# Hauptprogramm starten
def send_sensor_data():
    co2, temp_celsius, humidity = None, None, None
    try:
        while True:
            data = dev.read(0x81, 8, timeout=5000)
            op = data[0]
            val = (data[1] << 8) | data[2]

            if op == 0x50:
                co2 = val
            elif op == 0x42:
                temp_celsius = (val / 16.0) - 273.15
            elif op == 0x41:
                humidity = val / 100.0

            if co2 and temp_celsius and humidity:
                payload = {
                    "co2": co2,
                    "temperature": round(temp_celsius, 2),
                    "humidity": round(humidity, 2)
                }
                client.publish(DATA_TOPIC, json.dumps(payload))
                print(f"Gesendete Daten: {payload}")
                co2, temp_celsius, humidity = None, None, None

            time.sleep(30)

    except usb.core.USBError as e:
        print(f"USB-Fehler: {e}")

send_sensor_data()
