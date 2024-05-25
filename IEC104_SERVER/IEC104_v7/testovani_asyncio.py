import asyncio
import os
import sys

import tornado.ioloop

from MQTTProtocol import MQTTProtocol
import aiomqtt


class Test:
    def __init__(self):
        self.task = None
        self.mqtt_client_id: str = "192.168.1.10" + ':' + str(2404)
        self.mqtt_broker_ip: str = "192.168.1.167"
        self.mqtt_broker_port: int = 1883
        self.mqtt_topic: str = "Doma/Pokoj1/Stul"
        self.mqtt_version: int = 5
        self.mqtt_transport: str = "tcp"
        self.mqtt_username: str = "mqtt"
        self.mqtt_password: str = "MQTTpass123"
        self.mqtt_qos: int = 1
        # self.mqtt_client = MQTTProtocol(self.mqtt_client_id,
        #                                 self.mqtt_broker_ip,
        #                                 self.mqtt_broker_port,
        #                                 username=self.mqtt_username,
        #                                 password=self.mqtt_password,
        #                                 version=self.mqtt_version,
        #                                 transport=self.mqtt_transport,
        #                                 qos=self.mqtt_qos)
        self.data = b'\x0B\x07\x03\x00\x0C\x00\x10\x30\x00\xBE\x09\x00\x11\x30'

        self.async_loop = asyncio.get_running_loop()

    def start_mqtt(self):
        loop = asyncio.get_running_loop()
        # self.mqtt_client.start()

    async def start(self):

        try:
            # await self.mqtt_client.save_data(topic=self.mqtt_topic, data=self.data, callback=on_message)
            pass
        except Exception as e:
            print(f"Exception : {e}")

    # while True:
    #     await asyncio.sleep(5)
    #     print(f"run..")
    #
    #     await asyncio.sleep(2)
    #     await asyncio.gather(task, task1)
    # #


async def publish_temperature(client: aiomqtt.Client):
    await client.publish("Doma/Pokoj1/Stul", payload=28.4, qos=2)


async def publish_humidity(client):
    await client.publish("Doma/Pokoj1/Stul", payload=0.38, qos=2)


async def main():
    test = Test()
    async with aiomqtt.Client(hostname=test.mqtt_broker_ip,
                              username=test.mqtt_username,
                              password=test.mqtt_password,
                              ) as client:
        await publish_temperature(client)
        await publish_humidity(client)
        await client.subscribe(test.mqtt_topic)
        async for message in client.messages:
            await on_message(message)


async def on_message(topic, msg):
    print(f"message: {msg}")


if __name__ == '__main__':
    try:
        # Change to the "Selector" event loop if platform is Windows

        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        pass
