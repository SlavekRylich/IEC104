# -*- coding: utf-8 -*-
import asyncio
import paho.mqtt.client as mqtt
from IDataSharing import IDataSharing


class MQTTProtocol(IDataSharing):
    def __init__(self, client_id: str,
                 broker_url: str,
                 port: int,
                 username: str = None,
                 password: str = None,
                 version: int = None,
                 transport: str = None,
                 qos: int = 0
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
        self._port: int = port
        if version == 3:
            self._client = mqtt.Client(client_id=client_id,
                                       transport=transport,
                                       protocol=mqtt.MQTTv311,
                                       clean_session=True)

        if version == 5:
            self._client = mqtt.Client(client_id=client_id,
                                       transport=transport,
                                       protocol=mqtt.MQTTv5)
        else:
            raise Exception("Invalid MQTT version!")

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish
        self._client.on_subscribe = self._on_subscribe
        self._broker_url: str = broker_url
        self._qos: int = qos
        # self._client.tls_set()
        self._client.username_pw_set(username, password)
        self._username: str = username
        self._password: str = password
        self._connected: bool = False

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
        if rc == 0:
            self._connected = True
            print(f"Connected to MQTT Broker on {self._broker_url}:{self._port}")
        elif rc == 1:
            print(f"Connection refused – incorrect protocol version")
        elif rc == 2:
            print(f"Connection refused – invalid client identifier")
        elif rc == 3:
            print(f"Connection refused – server unavailable")
        elif rc == 4:
            print(f"Connection refused – bad username or password")
        elif rc == 5:
            print(f"Connection refused – not authorised")
        else:
            print(f"Bad connection: {rc}")

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
            print("mqtt client clearly Disconnected")
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
        print(f"Reason code from broker: {reason_code}"
              f"\nMid: {mid}")
        pass

    def _on_subscribe(self, client, userdata, mid, reason_code=None, properties=None):
        print(f"Subscribed back: \n client: {client}"
              f"userdata: {userdata}\n"
              f"mid: {mid}\n"
              f"rc: {reason_code}\n"
              f"properties: {properties}")

    async def connect(self, host, port, username, password):
        """
        Připojení klienta k brokerovi.
        """
        try:
            print(f"connect: {self._broker_url}")
            self._client.loop_start()
            self._client.connect(host=self._broker_url,
                                 port=self._port,
                                 keepalive=60)

        except Exception as e:
            print(f"mqtt client: Exception: {e}")

    async def disconnect(self):
        """
        Odpojení klienta od brokera.
        """
        self._client.loop_stop()
        self._client.disconnect()

    async def publish(self, topic: str, payload: str | bytes, qos: int = 0, retain=None):
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
        self._msg_info = self._client.publish(topic, payload, qos)
        print(type(payload))
        print(payload)
        print(f"Published to {topic}: {payload} with qos={qos}")
        self._unacked_publish.add(self._msg_info)
        self._msg_info.wait_for_publish(timeout=0.5)

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
                        data: bytes | bytearray | int | float | str | None,
                        callback=None):
        try:
            # """Ukládání dat do zprávy."""
            await self.connect(host=self._broker_url,
                               port=self._port,
                               username=self._username,
                               password=self._password)
            await self.publish(topic, payload=data, qos=self._qos, retain=None)

        except Exception as e:
            print(f"mqtt failed: {e}")

        finally:
            await self.disconnect()

    def send_data(self, callback):
        # """Odeslání zprávy."""
        pass
