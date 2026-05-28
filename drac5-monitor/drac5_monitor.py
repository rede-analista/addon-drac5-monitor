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
AVAIL = f'{DID}/availability'

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

# (chave no chassis status, sensor_id, nome, device_class)
CHASSIS_FAULTS = [
    ('Power Overload',   'power_overload',  'Power Overload',   'problem'),
    ('Main Power Fault', 'main_pwr_fault',  'Main Power Fault', 'problem'),
    ('Cooling/Fan Fault','cooling_fault',   'Cooling/Fan Fault','problem'),
    ('Drive Fault',      'drive_fault',     'Drive Fault',      'problem'),
    ('Chassis Intrusion','intrusion',       'Chassis Intrusion','tamper'),
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
        if len(parts) >= 3:
            result[parts[0]] = {'value': parts[1], 'status': parts[2]}
        elif len(parts) == 2:
            result[parts[0]] = {'value': parts[1], 'status': ''}
    return result


def parse_chassis():
    out = ipmi('chassis', 'status')
    result = {}
    for line in out.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            result[k.strip()] = v.strip().lower()
    return result


def get_sel_count():
    out = ipmi('sel', 'info')
    for line in out.splitlines():
        if line.strip().startswith('Entries') and ':' in line:
            return line.split(':', 1)[1].strip()
    return '0'


def get_sel_last():
    out = ipmi('sel', 'list')
    lines = [l for l in out.splitlines() if l.strip()]
    if not lines:
        return 'N/A'
    parts = [p.strip() for p in lines[-1].split('|')]
    if len(parts) >= 5:
        date = f"{parts[1]} {parts[2]}" if parts[1] != 'Pre-Init' else 'Pre-Init'
        desc = ' | '.join(parts[3:])
        return f"{date} — {desc}"[:255]
    return lines[-1].strip()[:255]


def publish_discovery(client):
    # Switch de energia
    client.publish(f'homeassistant/switch/{DID}/power/config', json.dumps({
        'name': 'Power',
        'unique_id': f'{DID}_power',
        'state_topic': f'{DID}/power/state',
        'command_topic': f'{DID}/power/set',
        'payload_on': 'ON',
        'payload_off': 'OFF',
        'availability_topic': AVAIL,
        'device': DEVICE,
        'icon': 'mdi:server-network',
    }), retain=True)

    # Temperatura ambiente
    client.publish(f'homeassistant/sensor/{DID}/ambient_temp/config', json.dumps({
        'name': 'Ambient Temperature',
        'unique_id': f'{DID}_ambient_temp',
        'state_topic': f'{DID}/sensor/ambient_temp',
        'device_class': 'temperature',
        'unit_of_measurement': '°C',
        'availability_topic': AVAIL,
        'device': DEVICE,
    }), retain=True)

    # Fans
    for _, sid, label in FAN_SENSORS:
        client.publish(f'homeassistant/sensor/{DID}/{sid}/config', json.dumps({
            'name': label,
            'unique_id': f'{DID}_{sid}',
            'state_topic': f'{DID}/sensor/{sid}',
            'unit_of_measurement': 'RPM',
            'icon': 'mdi:fan',
            'availability_topic': AVAIL,
            'device': DEVICE,
        }), retain=True)

    # Falhas do chassis
    for _, sid, label, dev_class in CHASSIS_FAULTS:
        client.publish(f'homeassistant/binary_sensor/{DID}/{sid}/config', json.dumps({
            'name': label,
            'unique_id': f'{DID}_{sid}',
            'state_topic': f'{DID}/binary_sensor/{sid}',
            'payload_on': 'ON',
            'payload_off': 'OFF',
            'device_class': dev_class,
            'availability_topic': AVAIL,
            'device': DEVICE,
        }), retain=True)

    # Redundância de fontes
    client.publish(f'homeassistant/binary_sensor/{DID}/ps_redundancy/config', json.dumps({
        'name': 'PS Redundancy Lost',
        'unique_id': f'{DID}_ps_redundancy',
        'state_topic': f'{DID}/binary_sensor/ps_redundancy',
        'payload_on': 'ON',
        'payload_off': 'OFF',
        'device_class': 'problem',
        'availability_topic': AVAIL,
        'device': DEVICE,
        'icon': 'mdi:lightning-bolt',
    }), retain=True)

    # Redundância de fans
    client.publish(f'homeassistant/binary_sensor/{DID}/fan_redundancy/config', json.dumps({
        'name': 'Fan Redundancy Lost',
        'unique_id': f'{DID}_fan_redundancy',
        'state_topic': f'{DID}/binary_sensor/fan_redundancy',
        'payload_on': 'ON',
        'payload_off': 'OFF',
        'device_class': 'problem',
        'availability_topic': AVAIL,
        'device': DEVICE,
        'icon': 'mdi:fan-alert',
    }), retain=True)

    # SEL — contagem de eventos
    client.publish(f'homeassistant/sensor/{DID}/sel_count/config', json.dumps({
        'name': 'Event Log Count',
        'unique_id': f'{DID}_sel_count',
        'state_topic': f'{DID}/sensor/sel_count',
        'unit_of_measurement': 'events',
        'icon': 'mdi:clipboard-list',
        'availability_topic': AVAIL,
        'device': DEVICE,
    }), retain=True)

    # SEL — último evento
    client.publish(f'homeassistant/sensor/{DID}/sel_last/config', json.dumps({
        'name': 'Last Event',
        'unique_id': f'{DID}_sel_last',
        'state_topic': f'{DID}/sensor/sel_last',
        'icon': 'mdi:clipboard-alert',
        'availability_topic': AVAIL,
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

client.will_set(AVAIL, 'offline', retain=True)
client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
client.subscribe(f'{DID}/power/set')
client.on_message = on_message
client.loop_start()

publish_discovery(client)
client.publish(AVAIL, 'online', retain=True)
print(f'INFO: DRAC5 Monitor v1.1.0 started — polling {IPMI_HOST} every {POLL}s')

while True:
    try:
        power = get_power()
        client.publish(f'{DID}/power/state', power)

        sdr = parse_sdr()

        # Temperatura ambiente
        if 'Ambient Temp' in sdr:
            m = re.search(r'(\d+)', sdr['Ambient Temp']['value'])
            if m:
                client.publish(f'{DID}/sensor/ambient_temp', m.group(1))

        # Fans
        for sdr_name, sid, _ in FAN_SENSORS:
            if sdr_name in sdr:
                m = re.search(r'(\d+)', sdr[sdr_name]['value'])
                if m:
                    client.publish(f'{DID}/sensor/{sid}', m.group(1))

        # Falhas do chassis
        chassis = parse_chassis()
        for chassis_key, sid, _, _ in CHASSIS_FAULTS:
            if chassis_key in chassis:
                state = 'ON' if chassis[chassis_key] in ('true', 'active') else 'OFF'
                client.publish(f'{DID}/binary_sensor/{sid}', state)

        # Redundância
        if 'PS Redundancy' in sdr:
            state = 'OFF' if sdr['PS Redundancy']['status'] == 'ok' else 'ON'
            client.publish(f'{DID}/binary_sensor/ps_redundancy', state)

        if 'Fan Redundancy' in sdr:
            state = 'OFF' if sdr['Fan Redundancy']['status'] == 'ok' else 'ON'
            client.publish(f'{DID}/binary_sensor/fan_redundancy', state)

        # SEL
        client.publish(f'{DID}/sensor/sel_count', get_sel_count())
        client.publish(f'{DID}/sensor/sel_last', get_sel_last())

    except Exception as e:
        print(f'ERROR: Poll failed: {e}')

    time.sleep(POLL)
