# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import paho.mqtt.client as mqtt


class MqttInterface(ABC):
    @abstractmethod
    def connect(self, host, port, username, password):
        # """Připojení k MQTT brokeru."""
        pass

    @abstractmethod
    def disconnect(self):
        """Odpojení od MQTT brokera."""
        pass

    @abstractmethod
    def publish(self, topic, message):
        """Odeslání zprávy do topicu."""
        pass

    @abstractmethod
    def subscribe(self, topic, callback):
        # """Přihlášení k odběru z topicu a nastavení funkce pro zpracování zpráv."""
        pass


class MqttPaho(MqttInterface):
    def __init__(self):
        self._client = mqtt.Client()

    def connect(self, host, port, username, password):
        self._client.connect(host, port, username, password)

    def disconnect(self):
        self._client.disconnect()

    def publish(self, topic, message):
        self._client.publish(topic, message)

    def subscribe(self, topic, callback):
        self._client.subscribe(topic, callback)


# class MqttAsyncio(MqttInterface):
#     def __init__(self):
#         self._client = aiomqtt.Client()
#
#     async def connect(self, host, port, username, password):
#         await self._client.connect(host, port, username, password)
#
#     async def disconnect(self):
#         await self._client.disconnect()
#
#     async def publish(self, topic, message):
#         await self._client.publish(topic, message)
#
#     async def subscribe(self, topic, callback):
#         await self._client.subscribe(topic, callback)


# Ukázka použití
def zpracuj_zpravu(topic, message):
    print(f"Zpráva z topicu '{topic}': {message}")


mqtt_interface = MqttPaho()
mqtt_interface.connect("localhost", 1883, "", "")
mqtt_interface.subscribe("topic", zpracuj_zpravu)

# # Asyncio
# client = aiomqtt.Client(hostname='192.168.1.136', port=1883)
# client.publish('/test', 'ahoy')
