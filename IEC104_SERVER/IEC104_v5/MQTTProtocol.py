import paho.mqtt.client as mqtt
import IDataSharing


class MQTTProtocol(IDataSharing):
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
        self._client = mqtt.Client(client_id)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._broker_url = broker_url
        self._port = port
        self._username = username
        self._password = password
        self._connected = False

    def _on_connect(self, client, userdata, flags, rc):
        """
        Metoda volan� po p�ipojen� klienta k brokerovi.

        Args:
            client: Klient MQTT.
            userdata: U�ivatelsk� data (nepou��v�no).
            flags: P��znaky p�ipojen�.
            rc: K�d n�vratu p�ipojen�.
        """
        self._connected = True

    def _on_message(self, client, userdata, message):
        """
        Metoda volan� po p�ijet� zpr�vy klientem.

        Args:
            client: Klient MQTT.
            userdata: U�ivatelsk� data (nepou��v�no).
            message: Zpr�va MQTT.
        """
        # Zpracov�n� p�ijat� zpr�vy
        pass

    def _on_disconnect(self, client, userdata, rc):
        """
        Metoda volan� po odpojen� klienta od brokera.

        Args:
            client: Klient MQTT.
            userdata: U�ivatelsk� data (nepou��v�no).
            rc: K�d n�vratu odpojen�.
        """
        self._connected = False

    def connect(self):
        """
        P�ipojen� klienta k brokerovi.
        """
        self._client.connect(self._broker_url, self._port, keepalive=60)
        self._client.loop_start()

    def disconnect(self):
        """
        Odpojen� klienta od brokera.
        """
        self._client.loop_stop()
        self._client.disconnect()

    def publish(self, topic: str, payload: bytes):
        """
        Publikov�n� zpr�vy na zadan� t�ma.

        Args:
            topic: T�ma zpr�vy.
            payload: Data zpr�vy.
        """
        self._client.publish(topic, payload)

    def subscribe(self, topic: str, callback):
        """
        P�ihl�en� k odb�ru zpr�v na zadan� t�ma.

        Args:
            topic: T�ma zpr�vy.
            callback: Funkce, kter� bude vol�na po p�ijet� zpr�vy.
        """
        self._client.subscribe(topic)
        self._client.on_message = callback

    def unsubscribe(self, topic: str):
        """
        Odhl�en� odb�ru zpr�v na zadan� t�ma.

        Args:
            topic: T�ma zpr�vy.
        """
        self._client.unsubscribe(topic)
