from abc import ABC, abstractmethod

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

    from paho.mqtt.client import Client

    class IMqttProtokol:
        def __init__(self, client_id: str, broker_url: str, port: int, username: str = None, password: str = None):
            """
            Inicializace klienta MQTT.

            Args:
                client_id: Identifik�tor klienta.
                broker_url: URL adresa brokera.
                port: Port brokera.
                username: U�ivatelsk� jm�no pro autentizaci (voliteln�).
                password: Heslo pro autentizaci (voliteln�).
            """
            self._client = Client(client_id)
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.on_disconnect = self._on_disconnect
            self._broker_url = broker_url
            self._port = port
            self._username = username
            self._password = password

        def _on_connect(self, client, userdata, flags, rc):
            """
            Metoda volan� po p�ipojen� klienta k brokerovi.

            Args:
                client: Klient MQTT.
                userdata: U�ivatelsk� data (nepou��v�no).
                flags: P��znaky p�ipojen�.
                rc: K�d n�vratu p�ipojen�.
            """
            raise NotImplementedError

        def _on_message(self, client, userdata, message):
            """
            Metoda volan� po p�ijet� zpr�vy klientem.

            Args:
                client: Klient MQTT.
                userdata: U�ivatelsk� data (nepou��v�no).
                message: Zpr�va MQTT.
            """
            raise NotImplementedError

        def _on_disconnect(self, client, userdata, rc):
            """
            Metoda volan� po odpojen� klienta od brokera.

            Args:
                client: Klient MQTT.
                userdata: U�ivatelsk� data (nepou��v�no).
                rc: K�d n�vratu odpojen�.
            """
            raise NotImplementedError

        def pripojit(self):
            """
            P�ipojen� klienta k brokerovi.
            """
            raise NotImplementedError

        def odpojit(self):
            """
            Odpojen� klienta od brokera.
            """
            raise NotImplementedError

        def publikovat(self, topic: str, payload: bytes, qos: int = 0, retain: bool = False):
            """
            Publikov�n� zpr�vy na zadan� t�ma.

            Args:
                topic: T�ma zpr�vy.
                payload: Data zpr�vy.
                qos: �rove� kvality slu�by (0, 1, 2).
                retain: True pro uchov�n� zpr�vy na brokerovi i po odpojen� klienta.
            """
            raise NotImplementedError

        def prihlasit_se(self):
            """
            P�ihl�en� klienta k brokerovi s u�ivatelsk�m jm�nem a heslem (pokud jsou definov�ny).
            """
            raise NotImplementedError

        def odhlasit_se(self):
            """
            Odhl�en� klienta od brokera.
            """
            raise NotImplementedError

