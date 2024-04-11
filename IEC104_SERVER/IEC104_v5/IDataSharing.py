from abc import ABC, abstractmethod
from paho.mqtt.client import Client

class IDataSharing(ABC):
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

    from paho.mqtt.client import Client


