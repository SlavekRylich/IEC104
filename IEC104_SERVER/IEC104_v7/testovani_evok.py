import asyncio
import os
import sys

import tornado.ioloop

from MQTTProtocol_tornado import MQTTProtocol_async
from MQTTProtocol import MQTTProtocol


class Test:
    def __init__(self, loop):
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
        self.mqtt_client = MQTTProtocol(self.mqtt_client_id,
                                        self.mqtt_broker_ip,
                                        self.mqtt_broker_port,
                                        username=self.mqtt_username,
                                        password=self.mqtt_password,
                                        version=self.mqtt_version,
                                        transport=self.mqtt_transport,
                                        qos=self.mqtt_qos)
        self.data = b'\x0B\x07\x03\x00\x0C\x00\x10\x30\x00\xBE\x09\x00\x11\x30'

        self.async_loop = loop

    def start_mqtt(self):
        loop = asyncio.get_running_loop()
        # self.mqtt_client.start()

    def start(self):

        self.mqtt_client.start(self.async_loop)
        try:

            self.async_loop.add_callback(lambda: self.mqtt_client.save_data(topic=self.mqtt_topic, data=self.data))

        # task = asyncio.ensure_future(test.mqtt_client.start(loop))
        #
        #     task1 = asyncio.create_task(test.mqtt_client.save_data(
        #         topic=test.mqtt_topic,
        #         data=str(test.data),
        #         callback=on_message))

        except Exception as e:
            print(f"Exception : {e}")

    # while True:
    #     await asyncio.sleep(5)
    #     print(f"run..")
    #
    #     await asyncio.sleep(2)
    #     await asyncio.gather(task, task1)
    # #


def main():
    mainLoop = tornado.ioloop.IOLoop.instance()
    test = Test(mainLoop)
    test.start()
    mainLoop.start()


def on_message(topic, msg):
    print(f"message: {msg}")


if __name__ == '__main__':
    try:

        main()
    except KeyboardInterrupt:
        pass
    finally:
        pass
