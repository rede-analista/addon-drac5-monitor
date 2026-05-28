ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache ipmitool python3 py3-pip bash

RUN pip3 install "paho-mqtt<2.0" --break-system-packages 2>/dev/null || pip3 install "paho-mqtt<2.0"

COPY run.sh /
COPY drac5_monitor.py /

RUN chmod +x /run.sh

CMD ["/run.sh"]
