import paho.mqtt.client as mqtt
import IDataSharing


class MQTTProtocol(IDataSharing):
    def __init__(self, client_id: str, broker_url: str, port: int, username: str = None, password: str = None):
        """
        Inicializace klienta MQTT.

        Args:
            client_id: Identifikátor klienta.
            broker_url: URL adresa brokera.
            port: Port brokera.
            username: Uživatelské jméno pro autentizaci (volitelnì).
            password: Heslo pro autentizaci (volitelnì).
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
        Metoda volaná po pøipojení klienta k brokerovi.

        Args:
            client: Klient MQTT.
            userdata: Uživatelská data (nepoužíváno).
            flags: Pøíznaky pøipojení.
            rc: Kód návratu pøipojení.
        """
        self._connected = True

    def _on_message(self, client, userdata, message):
        """
        Metoda volaná po pøijetí zprávy klientem.

        Args:
            client: Klient MQTT.
            userdata: Uživatelská data (nepoužíváno).
            message: Zpráva MQTT.
        """
        # Zpracování pøijaté zprávy
        pass

    def _on_disconnect(self, client, userdata, rc):
        """
        Metoda volaná po odpojení klienta od brokera.

        Args:
            client: Klient MQTT.
            userdata: Uživatelská data (nepoužíváno).
            rc: Kód návratu odpojení.
        """
        self._connected = False

    def connect(self):
        """
        Pøipojení klienta k brokerovi.
        """
        self._client.connect(self._broker_url, self._port, keepalive=60)
        self._client.loop_start()

    def disconnect(self):
        """
        Odpojení klienta od brokera.
        """
        self._client.loop_stop()
        self._client.disconnect()

    def publish(self, topic: str, payload: bytes):
        """
        Publikování zprávy na zadané téma.

        Args:
            topic: Téma zprávy.
            payload: Data zprávy.
        """
        self._client.publish(topic, payload)

    def subscribe(self, topic: str, callback):
        """
        Pøihlášení k odbìru zpráv na zadané téma.

        Args:
            topic: Téma zprávy.
            callback: Funkce, která bude volána po pøijetí zprávy.
        """
        self._client.subscribe(topic)
        self._client.on_message = callback

    def unsubscribe(self, topic: str):
        """
        Odhlášení odbìru zpráv na zadané téma.

        Args:
            topic: Téma zprávy.
        """
        self._client.unsubscribe(topic)
