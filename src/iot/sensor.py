import paho.mqtt.client as mqtt
import json
import time
import random  
from src.utils.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC

def on_connect(client, userdata, flags, rc):
    print(f"Conectado com o código {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(f"Mensagem recebida: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

while True:
    air_quality_data = {
        "sensor_id": "sensor_001",
        "timestamp": time.time(),
        "pm2.5": random.uniform(0, 100), 
        "pm10": random.uniform(0, 100)    
    }
    
    client.publish(MQTT_TOPIC, json.dumps(air_quality_data))
    time.sleep(60) 
