# DRAC 5 Monitor — Home Assistant Add-on

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Home Assistant add-on to monitor and control Dell servers with **DRAC 5 (Remote Access Controller 5)** via IPMI over LAN.

Designed for legacy Dell PowerEdge servers (e.g. 1950, 2950, 2900) where the DRAC 5 firmware has no further updates, the web interface is inaccessible due to old TLS, and modern iDRAC integrations (which require iDRAC 7/8 and the Redfish API) do not work.

---

## Features

- **Power switch** — turn the server on (IPMI `power on`) or off gracefully (IPMI `power soft`)
- **Ambient temperature sensor** — reads the chassis ambient temperature in °C
- **Fan speed sensors** — 16 RPM readings (FAN MOD 1A–4D)
- **MQTT auto-discovery** — all entities appear automatically in Home Assistant
- **Availability tracking** — entities go unavailable if the add-on stops

---

## Requirements

- Home Assistant OS (HAOS) or Supervised
- Mosquitto MQTT broker add-on (or any accessible MQTT broker)
- Network access from the HA host to the DRAC 5 IP on UDP port 623 (IPMI)
- DRAC 5 credentials (default: `root` / `calvin`)

---

## Installation

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**
2. Click the **⋮ menu** (top right) → **Repositories**
3. Add the repository URL:
   ```
   https://github.com/rede-analista/addon-drac5-monitor
   ```
4. Find **DRAC 5 Monitor** in the store and click **Install**

---

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `ipmi_host` | `172.31.254.99` | IP address of the DRAC 5 |
| `ipmi_user` | `root` | IPMI username |
| `ipmi_password` | `calvin` | IPMI password |
| `mqtt_host` | `core-mosquitto` | MQTT broker hostname |
| `mqtt_port` | `1883` | MQTT broker port |
| `mqtt_user` | `` | MQTT username (leave empty if not required) |
| `mqtt_password` | `` | MQTT password (leave empty if not required) |
| `poll_interval` | `30` | Sensor polling interval in seconds |

### Example configuration

```yaml
ipmi_host: "192.168.1.50"
ipmi_user: "root"
ipmi_password: "calvin"
mqtt_host: "core-mosquitto"
mqtt_port: 1883
mqtt_user: "ha_user"
mqtt_password: "secret"
poll_interval: 30
```

---

## Entities

All entities are grouped under the **Dell PowerEdge 1950** device in Home Assistant.

| Entity | Type | Description |
|--------|------|-------------|
| `switch.dell_poweredge_1950_power` | Switch | Power on / soft off |
| `sensor.dell_poweredge_1950_ambient_temperature` | Sensor | Chassis ambient temperature (°C) |
| `sensor.dell_poweredge_1950_fan_1a` … `fan_4d` | Sensor ×16 | Fan module RPM readings |

> **Note:** CPU temperature sensors are not available on DRAC 5 (reported as `ns` by IPMI).

---

## Compatibility

Tested on:

| Hardware | DRAC version | Firmware |
|----------|-------------|---------|
| Dell PowerEdge 1950 III | DRAC 5 | 1.65 (Build 12.08.16) |

Should also work on other PowerEdge models with DRAC 5 (e.g. 2950, 2900, 6950) as long as IPMI over LAN is enabled.

---

## License

[MIT](LICENSE) © Rede Analista
