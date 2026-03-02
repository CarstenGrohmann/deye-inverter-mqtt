import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from prettytable import PrettyTable
from datetime import datetime
#import json
import threading
import time

# Load environment variables from config.env
load_dotenv(dotenv_path='C:/Users/kalev/projects/akuu-energy-v3/backend-python/deye-inverter-mqtt/src/config.env')

MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_TOPIC_PREFIX = os.getenv('MQTT_TOPIC_PREFIX')

# Data structure to hold the latest received data for each object
# {
#   object_number: {
#     'time': value,
#     'power': value,
#     'soc': value,
#     'enabled': value,
#     'voltage': value
#   },
#   ...
# }
data_store = {i: {'time': None, 'power': None, 'soc': None, 'enabled': None, 'voltage': None} for i in range(1, 7)}
last_update_time = None
data_lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    if rc == 0:
        base_topic = f"{MQTT_TOPIC_PREFIX}/timeofuse"
        # Subscribe to all relevant topics
        for obj_num in range(1, 7):
            for param in ['time', 'power', 'soc', 'enabled', 'voltage']:
                topic = f"{base_topic}/{param}/{obj_num}"
                client.subscribe(topic)
                print(f"Subscribed to {topic}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global last_update_time
    try:
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 3 and topic_parts[-3] == 'timeofuse':
            object_param = topic_parts[-2]
            object_number = int(topic_parts[-1])
            value = msg.payload.decode()

            with data_lock:
                if object_number in data_store:
                    # Attempt to convert to appropriate type
                    if object_param in ['power', 'soc', 'voltage']:
                        value = int(float(value))
                    elif object_param == 'enabled':
                        value = bool(int(float(value))) # Assuming '0' or '1' for boolean
                    # 'time' can remain a string or be parsed into a datetime object if needed

                    data_store[object_number][object_param] = value
                    last_update_time = datetime.now()
                else:
                    print(f"Received data for unknown object number: {object_number}")
        else:
            print(f"Received message on unexpected topic: {msg.topic}")

    except Exception as e:
        print(f"Error processing message: {e}")
        print(f"Topic: {msg.topic}, Payload: {msg.payload.decode()}")

def display_table():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear') # Clear console
        table = PrettyTable()
        table.field_names = ["Object Number", "Time", "Power", "SoC", "Enabled", "Voltage"]

        with data_lock:
            for obj_num in sorted(data_store.keys()):
                obj_data = data_store[obj_num]
                table.add_row([
                    obj_num,
                    obj_data['time'] if obj_data['time'] is not None else 'wait',
                    obj_data['power'] if obj_data['power'] is not None else 'wait',
                    obj_data['soc'] if obj_data['soc'] is not None else 'wait',
                    obj_data['enabled'] if obj_data['enabled'] is not None else 'wait',
                    obj_data['voltage'] if obj_data['voltage'] is not None else 'wait'
                ])

            print("Time of Use Objects Data")
            print(table)
            if last_update_time:
                print(f"\nLast Updated: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("\nWaiting for data...")

        time.sleep(1) # Refresh every 1 second

def main():
    client = mqtt.Client()
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")
        return

    # Start the MQTT client loop in a separate thread to handle incoming messages
    mqtt_thread = threading.Thread(target=client.loop_forever)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    # Start the display table thread
    display_thread = threading.Thread(target=display_table)
    display_thread.daemon = True
    display_thread.start()

    # Keep the main thread alive to allow daemon threads to run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting application.")
        client.disconnect()

if __name__ == "__main__":
    main()
