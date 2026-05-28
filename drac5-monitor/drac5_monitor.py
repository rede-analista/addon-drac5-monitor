#!/usr/bin/env python3
import subprocess
import json
import time
import re
import paho.mqtt.client as mqtt

with open('/data/options.json') as f:
    cfg = json.load(f)

IPMI_HOST = cfg['ipmi_host']
IPMI_USER = cfg['ipmi_user']
IPMI_PASS = cfg['ipmi_password']
MQTT_HOST = cfg['mqtt_host']
MQTT_PORT = int(cfg.get('mqtt_port', 1883))
MQTT_USER = cfg.get('mqtt_user', '')
MQTT_PASS = cfg.get('mqtt_password', '')
POLL = int(cfg.get('poll_interval', 30))

DID = 'drac5_poweredge'

DEVICE = {
    'identifiers': [DID],
    'name': 'Dell PowerEdge 1950',
    'model': 'PowerEdge 1950 III',
    'manufacturer': 'Dell',
    'sw_version': 'DRAC 5 v1.65',
}

FAN_SENSORS = [
    ('FAN MOD 1A RPM', 'fan_1a', 'Fan 1A'),
    ('FAN MOD 1B RPM', 'fan_1b', 'Fan 1B'),
    ('FAN MOD 1C RPM', 'fan_1c', 'Fan 1C'),
    ('FAN MOD 1D RPM', 'fan_1d', 'Fan 1D'),
    ('FAN MOD 2A RPM', 'fan_2a', 'Fan 2A'),
    ('FAN MOD 2B RPM', 'fan_2b', 'Fan 2B'),
    ('FAN MOD 2C RPM', 'fan_2c', 'Fan 2C'),
    ('FAN MOD 2D RPM', 'fan_2d', 'Fan 2D'),
    ('FAN MOD 3A RPM', 'fan_3a', 'Fan 3A'),
    ('FAN MOD 3B RPM', 'fan_3b', 'Fan 3B'),
    ('FAN MOD 3C RPM', 'fan_3c', 'Fan 3C'),
    ('FAN MOD 3D RPM', 'fan_3d', 'Fan 3D'),
    ('FAN MOD 4A RPM', 'fan_4a', 'Fan 4A'),
    ('FAN MOD 4B RPM', 'fan_4b', 'Fan 4B'),
    ('FAN MOD 4C RPM', 'fan_4c', 'Fan 4C'),
    ('FAN MOD 4D RPM', 'fan_4d', 'Fan 4D'),
]


def ipmi(*args):
    r = subprocess.run(
        ['ipmitool', '-I', 'lanplus', '-H', IPMI_HOST,
         '-U', IPMI_USER, '-P', IPMI_PASS, *args],
        capture_output=True, text=True, timeout=20
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or 'ipmitool error')
    return r.stdout.strip()


def get_power():
    out = ipmi('power', 'status')
    return 'ON' if 'on' in out.lower() else 'OFF'


def parse_sdr():
    out = ipmi('sdr', 'list')
    result = {}
    for line in out.splitlines():
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2:
            result[parts[0]] = parts[1]
    return result


def publish_discovery(client):
    avail = f'{DID}/availability'

    client.publish(f'homeassistant/switch/{DID}/power/config', json.dumps({
        'name': 'Power',
        'unique_id': f'{DID}_power',
        'state_topic': f'{DID}/power/state',
        'command_topic': f'{DID}/power/set',
        'payload_on': 'ON',
        'payload_off': 'OFF',
        'availability_topic': avail,
        'device': DEVICE,
        'icon': 'mdi:server-network',
    }), retain=True)

    client.publish(f'homeassistant/sensor/{DID}/ambient_temp/config', json.dumps({
        'name': 'Ambient Temperature',
        'unique_id': f'{DID}_ambient_temp',
        'state_topic': f'{DID}/sensor/ambient_temp',
        'device_class': 'temperature',
        'unit_of_measurement': '°C',
        'availability_topic': avail,
        'device': DEVICE,
    }), retain=True)

    for _, sid, label in FAN_SENSORS:
        client.publish(f'homeassistant/sensor/{DID}/{sid}/config', json.dumps({
            'name': label,
            'unique_id': f'{DID}_{sid}',
            'state_topic': f'{DID}/sensor/{sid}',
            'unit_of_measurement': 'RPM',
            'icon': 'mdi:fan',
            'availability_topic': avail,
            'device': DEVICE,
        }), retain=True)


def on_message(client, userdata, msg):
    cmd = msg.payload.decode().strip()
    try:
        if cmd == 'ON':
            print('INFO: Power ON command received')
            ipmi('power', 'on')
        elif cmd == 'OFF':
            print('INFO: Power OFF (soft) command received')
            ipmi('power', 'soft')
    except Exception as e:
        print(f'ERROR: Power command failed: {e}')


client = mqtt.Client()
if MQTT_USER:
    client.username_pw_set(MQTT_USER, MQTT_PASS)

client.will_set(f'{DID}/availability', 'offline', retain=True)
client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
client.subscribe(f'{DID}/power/set')
client.on_message = on_message
client.loop_start()

publish_discovery(client)
client.publish(f'{DID}/availability', 'online', retain=True)
print(f'INFO: DRAC5 Monitor started — polling {IPMI_HOST} every {POLL}s')

while True:
    try:
        power = get_power()
        client.publish(f'{DID}/power/state', power)

        sdr = parse_sdr()

        if 'Ambient Temp' in sdr:
            m = re.search(r'(\d+)', sdr['Ambient Temp'])
            if m:
                client.publish(f'{DID}/sensor/ambient_temp', m.group(1))

        for sdr_name, sid, _ in FAN_SENSORS:
            if sdr_name in sdr:
                m = re.search(r'(\d+)', sdr[sdr_name])
                if m:
                    client.publish(f'{DID}/sensor/{sid}', m.group(1))

    except Exception as e:
        print(f'ERROR: Poll failed: {e}')

    time.sleep(POLL)
