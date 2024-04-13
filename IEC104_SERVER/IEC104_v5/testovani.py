import asyncio
import struct

from MQTTProtocol import MQTTProtocol


class Class:
    def __init__(self):
        # MQTT client
        self.__ip = "127.0.0.1"
        self.__port = 45656
        self.__name = "Class"
        self.__server_name = "Server"
        self.__mqtt_topic: str | None = '/' + self.__server_name + '/' + self.__name  # "Server/ClientX
        self.__mqtt_client_id: str = self.__ip + ':' + str(self.__port)
        # self.__mqtt_broker: str | None = "localhost"
        self.__mqtt_broker: str | None = "192.168.1.136"
        self.__mqtt_port: int | None = 1883
        self.__mqtt_client = MQTTProtocol(self.__mqtt_client_id, self.__mqtt_broker, self.__mqtt_port)

        self.data2 = struct.pack(f"{'B' * 10}",
                                 0x65,
                                 0x01,
                                 0x0A,
                                 0x00,
                                 0x0C,
                                 0x00,
                                 0x00,
                                 0x00,
                                 0x00,
                                 0x05,
                                 )

    async def main(self):
        data = self.data2
        await self.__mqtt_client.save_data(topic=self.__mqtt_topic + f"/Session_1",
                                           data=self.data2,
                                           callback=None)


if __name__ == "__main__":

    # host = "192.168.1.142"
    # host = "192.168.1.136"
    host = "127.0.0.1"
    port = 2404

    client = Class()
    try:
        asyncio.run(client.main())
    except KeyboardInterrupt:
        pass
    finally:
        pass
