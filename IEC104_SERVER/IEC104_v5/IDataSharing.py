from abc import ABC, abstractmethod
from paho.mqtt.client import Client

class IDataSharing(ABC):
    @abstractmethod
    def connect(self, host, port, username, password):
        # """Pøipojení k MQTT brokeru."""
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
        # """Pøihlášení k odbìru z topicu a nastavení funkce pro zpracování zpráv."""
        pass

    from paho.mqtt.client import Client


