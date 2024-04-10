import asyncio
import random
import time

from aiomqtt import Client, MqttError
import paho.mqtt.client as mqtt

MQTT_HOST = "192.168.1.142"
MQTT_PORT = 1883
qos = 0

MQTT_TOPIC = f"/test"


# Sample async function to be called
async def processSnapshot(camera_serial):
    print("processSnapshot")
    await asyncio.sleep(1)


# This gets called whenever when we get an MQTT message
async def mqtt_on_message(msg):
    print("process")
    # ...
    # data = json.loads(msg.payload.decode('utf-8'))
    # split_topic = msg.topic.split("/", 3)
    # ...

    print("processSnapshot")


def gen_payload(sender: str, qos: int) -> str:
    """Generate random payload."""
    time_r = time.time()
    return (
        f'{{"sender":"{sender}", '
        f'"qos":{qos}, '
        f'"value":{random.random() * 100:.2f}, '
        f'"time":"{time_r}"}}'
    )


def on_connect(
        client, userdata, flags, rc
) -> None:  # noqa: ANN001, ARG001
    print("Connected with result code " + str(rc))
    client.subscribe("$SYS/#")


def on_message(client, userdata, msg) -> None:  # noqa: ANN001, ARG001
    print(msg.MQTT_TOPIC + " " + str(msg.payload))


def on_publish(mosq, obj, mid) -> None:  # noqa: ANN001, ARG001
    print("mid: " + str(mid))


def on_subscribe(
        mosq, obj, mid, granted_qos
) -> None:  # noqa: ANN001, ARG001
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


async def main():
    payload = gen_payload("paho", qos)


    client = mqtt.Client()

    # Assign event callbacks
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe

    client.username_pw_set(username='USERNAME', password='MQTT_PASSWORD')
    client.connect(host=MQTT_HOST, port=MQTT_PORT, keepalive=60)
    client.subscribe(MQTT_TOPIC, qos=qos)

    msginfo = client.publish(topic=MQTT_TOPIC, payload=payload, qos=qos)
    msginfo.wait_for_publish(0.1)
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
        print(f"returned code: {msginfo.rc}: {emsg}")
    client.disconnect()
    print("DONE!")
    await send_via_aiomqtt(qos)


async def send_via_aiomqtt(qos_param) -> None:
    """Send value via aiomqtt."""
    mqtt_client = Client(
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        timeout=3,
    )

    topic = MQTT_TOPIC
    payload = gen_payload("aiomqtt", qos_param)
    try:
        print(mqtt_client.identifier)
        print(f"Subscribing to: {topic}")
        await mqtt_client.subscribe(topic, qos=qos_param)
        print(f"Publishing to: {topic} -> {payload}")
        await mqtt_client.publish(topic, payload=payload, qos=qos_param)

    except MqttError as e:
        print(f"MqttError: {e}")
    except Exception as e:
        print(f"Exception: {e}")

    # async with mqtt_client as client:
    #     print(f"Subscribing to: {topic}")
    #     await client.subscribe(topic, qos=qos_param)
    #     print(f"Publishing to: {topic} -> {payload}")
    #     await client.publish(topic, payload=payload, qos=qos_param)
    print("DONE!")


if __name__ == "__main__":
    # execute only if run as a script
    asyncio.run(main())
