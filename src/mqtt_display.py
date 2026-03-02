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
# Data structure to hold general metrics
general_metrics_store = {
    'battery/power': None,
    'battery/soc': None,
    'ac/total_power': None,
    'ac/ups/total_power': None,
    'settings/battery/maximum_charge_current': None,
    'settings/battery/maximum_discharge_current': None,
    'settings/battery/maximum_grid_charge_current': None,
    'settings/battery/grid_charge': None,
    'settings/workmode': None,
    'settings/solar_sell': None,
}
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

        # Subscribe to general metrics topics
        general_topics = [
            'battery/power',
            'battery/soc',
            'ac/total_power',
            'ac/ups/total_power',
            'settings/battery/maximum_charge_current',
            'settings/battery/maximum_discharge_current',
            'settings/battery/maximum_grid_charge_current',
            'settings/battery/grid_charge',
            'settings/workmode',
            'settings/solar_sell',
        ]
        for gt in general_topics:
            topic = f"{MQTT_TOPIC_PREFIX}/{gt}"
            client.subscribe(topic)
            print(f"Subscribed to {topic}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global last_update_time
    try:
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 3 and topic_parts[-3] == 'timeofuse':
            process_timeofuse(topic_parts, msg.payload.decode())
        elif msg.topic.startswith(f"{MQTT_TOPIC_PREFIX}/"):
            # Check for general metrics
            suffix = msg.topic[len(f"{MQTT_TOPIC_PREFIX}/"):]
            if suffix in general_metrics_store:
                process_general_metric(suffix, msg.payload.decode())
            else:
                print(f"Received message on unhandled topic: {msg.topic}")
        else:
            print(f"Received message on unexpected topic: {msg.topic}")

    except Exception as e:
        print(f"Error processing message: {e}")
        print(f"Topic: {msg.topic}, Payload: {msg.payload.decode()}")


def process_timeofuse(topic_parts: list, payload: str):
    global last_update_time
    object_param = topic_parts[-2]
    object_number = int(topic_parts[-1])
    value = payload
    with data_lock:
        if object_number in data_store:
            # Attempt to convert to appropriate type
            if object_param in ['power', 'soc', 'voltage', 'time']:
                try:
                    value = int(float(value))
                except ValueError:
                    value = value # keep as string if conversion fails
            elif object_param == 'enabled':
                try:
                    value = bool(int(float(value)))  # Assuming '0' or '1' for boolean
                except ValueError:
                    value = value # keep as string if conversion fails

            data_store[object_number][object_param] = value
            last_update_time = datetime.now()
        else:
            print(f"Received data for unknown object number: {object_number}")

def process_general_metric(metric_key, value_str):
    global last_update_time
    with data_lock:
        try:
            # Attempt to convert to appropriate type
            if metric_key in ['battery/power', 'battery/soc', 'ac/total_power', 'ac/ups/total_power',
                             'settings/battery/maximum_charge_current', 'settings/battery/maximum_discharge_current',
                             'settings/battery/maximum_grid_charge_current']:
                value = float(value_str)
            elif metric_key in ['settings/battery/grid_charge', 'settings/solar_sell']:
                value = bool(int(float(value_str))) # Assuming '0' or '1'
            elif metric_key == 'settings/workmode':
                value = value_str # Keep as string
            else:
                value = value_str # Default to string for unknown types

            general_metrics_store[metric_key] = value
            last_update_time = datetime.now()
        except ValueError:
            print(f"Could not convert value '{value_str}' for metric '{metric_key}'. Keeping as string.")
            general_metrics_store[metric_key] = value_str


def display_table():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear') # Clear console
        table = PrettyTable()
        table.field_names = ["Object Number", "Time", "Power", "SoC", "Enabled", "Voltage"]

        with data_lock:
            print("General Metrics:")
            general_metrics_table = PrettyTable()
            general_metrics_table.field_names = ["Metric", "Value"]
            for key in sorted(general_metrics_store.keys()):
                value = general_metrics_store[key]
                general_metrics_table.add_row([key, value if value is not None else 'N/A'])
            print(general_metrics_table)
            print("\n" + "="*50 + "\n") # Separator

            print("Time of Use Objects Data")
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
