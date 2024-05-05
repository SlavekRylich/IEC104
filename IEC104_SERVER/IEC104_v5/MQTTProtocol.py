# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
from IDataSharing import IDataSharing


class MQTTProtocol(IDataSharing):
    def __init__(self, client_id: str,
                 broker_url: str,
                 port: int,
                 username: str = None,
                 password: str = None
                 ):
        """
        Inicializace klienta MQTT.

        Args:
            client_id: Identifikátor klienta.
            broker_url: URL adresa brokera.
            port: Port brokera.
            username: Uživatelské jméno pro autentizaci (volitelně).
            password: Heslo pro autentizaci (volitelně).
        """

        self._msg_info: mqtt.MQTTMessage | None = None
        self._client = mqtt.Client(client_id=client_id, protocol=5)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish
        self._broker_url = broker_url
        self._port = port
        self._username = username
        self._password = password
        self._connected = False

        self._unacked_publish = set()
        self._client.user_data_set(self._unacked_publish)

    def _on_connect(self, client, userdata, flags, rc, properties):
        """
        Metoda volaná po připojení klienta k brokerovi.

        Args:
            client: Klient MQTT.
            userdata: Uživatelská data (nepoužíváno).
            flags: Příznaky připojení.
            rc: Kód návratu připojení.
        """
        self._connected = True
        print(f"Connected to MQTT Broker on {self._broker_url}")

    def _on_message(self, client, userdata, message):
        """
        Metoda volaná po přijetí zprávy klientem.

        Args:
            client: Klient MQTT.
            userdata: Uživatelská data (nepoužíváno).
            message: Zpráva MQTT.
        """
        # Zpracování přijaté zprávy
        print(f"Receive message via MQTT {message}")
        pass

    def _on_disconnect(self, client, userdata, rc, properties):
        """
        Metoda volaná po odpojení klienta od brokera.

        Args:
            client: Klient MQTT.
            userdata: Uživatelská data (nepoužíváno).
            rc: Kód návratu odpojení.
        """
        if rc == 0:
            self._connected = False
            print("mqtt client: Disconnected")
        else:
            print(f"Disconnected from MQTT broker.")

    def _on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        """
        Metoda volaná po ukládání dat do zprávy.

        Args:
            client: Klient MQTT.
            userdata: Uživatelská data (nepoužíváno).
            mid: Identifikátor zprávy.
            reason_code: Kód návratu ukládání dat do zprávy.
            properties: Vlastnosti zprávy.
        """
        print(f"Published message to broker {userdata}")
        pass

    async def connect(self):
        """
        Připojení klienta k brokerovi.
        """
        try:
            print(f"connect: {self._broker_url}")
            self._client.connect(host=self._broker_url, port=self._port, keepalive=60)
            self._client.loop_start()
        except Exception as e:
            print(f"mqtt client: Exception: {e}")

    async def disconnect(self):
        """
        Odpojení klienta od brokera.
        """
        self._client.loop_stop()
        self._client.disconnect()

    async def publish(self, topic: str, payload: bytes, qos: int = 0, retain=None):
        """
        Publikování zprávy na zadané téma.

        Args:
            topic: Téma zprávy.
            payload: Data zprávy.
            :param topic:
            :param payload:
            :param qos:
            :param retain:
        """
        print(f"To publish {payload}")
        self._msg_info = self._client.publish(topic, payload, qos)
        print(f"Published to {topic}: {payload} with qos={qos}")
        self._unacked_publish.add(self._msg_info)
        self._msg_info.wait_for_publish(timeout=0.2)

    async def subscribe(self, topic: str, callback):
        """
        Přihlášení k odběru zpráv na zadané téma.

        Args:
            topic: Téma zprávy.
            callback: Funkce, která bude volána po přijetí zprávy.
        """
        self._client.subscribe(topic)
        self._client.on_message = callback

    def unsubscribe(self, topic: str):
        """
        Odhlášení odběru zpráv na zadané téma.

        Args:
            topic: Téma zprávy.
        """
        self._client.unsubscribe(topic)

    async def save_data(self,
                        topic: str,
                        data: bytes | bytearray | int | float | str| None,
                        callback=None):
        # """Ukládání dat do zprávy."""
        await self.connect()
        await self.publish(topic, payload=data, qos=1, retain=None)
        await self.disconnect()

    def send_data(self, callback):
        # """Odeslání zprávy."""
        pass
