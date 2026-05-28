# DRAC 5 Monitor — Add-on para Home Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Add-on para Home Assistant para monitorar e controlar servidores Dell com **DRAC 5 (Remote Access Controller 5)** via IPMI over LAN.

Desenvolvido para servidores Dell PowerEdge legados (ex: 1950, 2950, 2900) onde o firmware do DRAC 5 não recebe mais atualizações, a interface web é inacessível por problemas de TLS antigo, e integrações modernas de iDRAC (que exigem iDRAC 7/8 e a API Redfish) não funcionam.

---

## Funcionalidades

- **Switch de energia** — liga o servidor (IPMI `power on`) ou desliga de forma segura (IPMI `power soft`)
- **Sensor de temperatura ambiente** — lê a temperatura ambiente do chassi em °C
- **Sensores de velocidade dos fans** — 16 leituras de RPM (FAN MOD 1A–4D)
- **Auto-discovery MQTT** — todas as entidades aparecem automaticamente no Home Assistant
- **Rastreamento de disponibilidade** — entidades ficam indisponíveis se o add-on parar

---

## Requisitos

- Home Assistant OS (HAOS) ou Supervised
- Add-on Mosquitto MQTT Broker (ou qualquer broker MQTT acessível)
- Acesso de rede do host do HA ao IP do DRAC 5 na porta UDP 623 (IPMI)
- Credenciais do DRAC 5 (padrão Dell: `root` / `calvin`)

---

## Instalação

1. No Home Assistant, acesse **Configurações → Add-ons → Loja de Add-ons**
2. Clique no menu **⋮** (canto superior direito) → **Repositórios**
3. Adicione a URL do repositório:
   ```
   https://github.com/rede-analista/addon-drac5-monitor
   ```
4. Localize **DRAC 5 Monitor** na loja e clique em **Instalar**

---

## Configuração

| Opção | Padrão | Descrição |
|-------|--------|-----------|
| `ipmi_host` | `172.31.254.99` | Endereço IP do DRAC 5 |
| `ipmi_user` | `root` | Usuário IPMI |
| `ipmi_password` | `calvin` | Senha IPMI |
| `mqtt_host` | `core-mosquitto` | Hostname do broker MQTT |
| `mqtt_port` | `1883` | Porta do broker MQTT |
| `mqtt_user` | `` | Usuário MQTT (deixar vazio se não necessário) |
| `mqtt_password` | `` | Senha MQTT (deixar vazio se não necessário) |
| `poll_interval` | `30` | Intervalo de leitura dos sensores em segundos |

### Exemplo de configuração

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

## Entidades

Todas as entidades são agrupadas sob o dispositivo **Dell PowerEdge 1950** no Home Assistant.

### Controle

| Entidade | Tipo | Descrição |
|----------|------|-----------|
| `switch.dell_poweredge_1950_power` | Switch | Liga (`power on`) / desliga com segurança (`power soft`) |

### Sensores

| Entidade | Tipo | Descrição |
|----------|------|-----------|
| `sensor.dell_poweredge_1950_ambient_temperature` | Sensor | Temperatura ambiente do chassi (°C) |
| `sensor.dell_poweredge_1950_fan_1a` … `fan_4d` | Sensor ×16 | Velocidade dos módulos de fan (RPM) |
| `sensor.dell_poweredge_1950_event_log_count` | Sensor | Número total de eventos no log do sistema (SEL) |
| `sensor.dell_poweredge_1950_last_event` | Sensor | Descrição do último evento registrado no SEL |

### Sensores binários (falhas)

| Entidade | Tipo | Descrição |
|----------|------|-----------|
| `binary_sensor.dell_poweredge_1950_cooling_fan_fault` | Binary sensor | Falha de resfriamento/fan detectada |
| `binary_sensor.dell_poweredge_1950_drive_fault` | Binary sensor | Falha de disco detectada |
| `binary_sensor.dell_poweredge_1950_power_overload` | Binary sensor | Sobrecarga de energia detectada |
| `binary_sensor.dell_poweredge_1950_main_power_fault` | Binary sensor | Falha de energia principal |
| `binary_sensor.dell_poweredge_1950_chassis_intrusion` | Binary sensor | Intrusão no chassi (tampa aberta) |
| `binary_sensor.dell_poweredge_1950_ps_redundancy_lost` | Binary sensor | Redundância de fontes de alimentação perdida |
| `binary_sensor.dell_poweredge_1950_fan_redundancy_lost` | Binary sensor | Redundância de fans perdida |

> **Observação:** sensores de temperatura da CPU não estão disponíveis no DRAC 5 (reportados como `ns` pelo IPMI).

---

## Compatibilidade

Testado em:

| Hardware | Versão DRAC | Firmware |
|----------|-------------|---------|
| Dell PowerEdge 1950 III | DRAC 5 | 1.65 (Build 12.08.16) |

Deve funcionar também em outros modelos PowerEdge com DRAC 5 (ex: 2950, 2900, 6950), desde que o IPMI over LAN esteja habilitado.

---

## Licença

[MIT](LICENSE) © Rede Analista
