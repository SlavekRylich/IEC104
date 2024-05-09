# -*- coding: utf-8 -*-

"""Testing paho / aiomqtt behaviour."""
import argparse
import asyncio
import os
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt
from aiomqtt import Client, MqttError
# from loguru import logger
import logging as logger


tz: int = time.timezone

MQTT_HOST: str = "192.168.1.136"
MQTT_PORT: int = 1883


def get_parser() -> argparse.ArgumentParser:
    """Add QoS parameter handler."""
    parser = argparse.ArgumentParser(
        prog="mq",
        description="Testing different paho MQTT libraries",
    )
    parser.add_argument("-q", "--qos", type=int, required=True, metavar="QoS")
    return parser


def gen_payload(sender: str, qos: int) -> str:
    """Generate random payload."""
    time_r = time.time()
    return (
        f'{{"sender":"{sender}", '
        f'"qos":{qos}, '
        f'"value":{random.random() * 100:.2f}, '
        f'"time":"{time_r}"}}'
    )


def send_via_paho(qos) -> None:
    """Send value via paho."""

    def on_connect(
        client, userdata, flags, rc
    ) -> None:  # noqa: ANN001, ARG001
        logger.info("Connected with result code " + str(rc))
        client.subscribe("$SYS/#")

    def on_message(client, userdata, msg) -> None:  # noqa: ANN001, ARG001
        logger.info(msg.MQTT_TOPIC + " " + str(msg.payload))

    def on_publish(mosq, obj, mid) -> None:  # noqa: ANN001, ARG001
        logger.info("mid: " + str(mid))

    def on_subscribe(
        mosq, obj, mid, granted_qos
    ) -> None:  # noqa: ANN001, ARG001
        logger.info("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_log(mosq, obj, level, string) -> None:  # noqa: ANN001, ARG001
        logger.info(string)

    client = mqtt.Client()

    # Assign event callbacks
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe

    topic = f"{MQTT_TOPIC}/sys/cpu/percent"
    payload = gen_payload("paho", qos)

    client.username_pw_set(username=USERNAME, password=MQTT_PASSWORD)
    client.connect(host=MQTT_HOST, port=MQTT_PORT, keepalive=60)
    client.subscribe(topic, qos=qos)

    msginfo = client.publish(topic=topic, payload=payload, qos=qos)
    msginfo.wait_for_publish()
    if msginfo.rc != 0:
        # MQTTClient_connect()
        # https://www.eclipse.org/paho/files/mqttdoc/MQTTClient/html/_m_q_t_t_client_8h.html#aaa8ae61cd65c9dc0846df10122d7bd4e
        err_code = {
            1: "Connection refused: Unacceptable protocol version",
            2: "Connection refused: Identifier rejected",
            3: "Connection refused: Server unavailable",
            4: "Connection refused: Bad user name or password",
            5: "Connection refused: Not authorized",
        }
        emsg = (
            err_code[msginfo.rc]
            if msginfo.rc in err_code
            else "Error code not handled yet..."
        )
        logger.warning(f"returned code: {msginfo.rc}: {emsg}")
    client.disconnect()
    logger.info("DONE!")


async def send_via_aiomqtt(qos) -> None:
    """Send value via aiomqtt."""
    mqtt_client = Client(
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        timeout=3,
    )

    topic = f"{MQTT_TOPIC}/sys/cpu/percent"
    payload = gen_payload("aiomqtt", qos)
    async with mqtt_client as client:
        logger.info(f"Subscribing to: {topic}")
        await client.subscribe(topic, qos=qos)
        logger.info(f"Publishing to: {topic} -> {payload}")
        await client.publish(topic, payload=payload, qos=qos)
    logger.info("DONE!")


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    send_via_paho(args.qos)
    asyncio.run(send_via_aiomqtt(args.qos))