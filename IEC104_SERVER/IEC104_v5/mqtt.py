from abc import ABC, abstractmethod
import asyncio_mqtt as aiomqtt
import paho.mqtt.client as mqtt


class MqttInterface(ABC):
    @abstractmethod
    def connect(self, host, port, username, password):
        # """P�ipojen� k MQTT brokeru."""
        pass

    @abstractmethod
    def disconnect(self):
        """Odpojen� od MQTT brokera."""
        pass

    @abstractmethod
    def publish(self, topic, message):
        """Odesl�n� zpr�vy do topicu."""
        pass

    @abstractmethod
    def subscribe(self, topic, callback):
        # """P�ihl�en� k odb�ru z topicu a nastaven� funkce pro zpracov�n� zpr�v."""
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


# Uk�zka pou�it�
def zpracuj_zpravu(topic, message):
    print(f"Zpr�va z topicu '{topic}': {message}")


mqtt_interface = MqttPaho()
mqtt_interface.connect("localhost", 1883, "", "")
mqtt_interface.subscribe("topic", zpracuj_zpravu)

# # Asyncio
# client = aiomqtt.Client(hostname='192.168.1.136', port=1883)
# client.publish('/test', 'ahoy')
