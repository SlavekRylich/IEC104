# -*- coding: utf-8 -*-
import os

import asyncio

# import paho.mqtt.client as mqtt
# from asyncio_mqtt import ProtocolVersion

from IDataSharing import IDataSharing
from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311, MQTTv50


class MQTTProtocol_async_gmqtt(IDataSharing):
    """
    MQTTProtocol class for handling MQTT communication.
    """

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
        Initialize MQTTProtocol instance.

        :param client_id: MQTT client ID.
        :param broker_url: MQTT broker URL.
        :param port: MQTT broker port.
        :param username: MQTT broker username.
        :param password: MQTT broker password.
        :param version: MQTT protocol version.
        :param transport: MQTT transport protocol.
        :param qos: MQTT Quality of Service level.
        """

        # self._msg_info: mqtt.MQTTMessage | None = None
        self._port: int = port
        self._username: str = username
        self._password: str = password
        self._broker_url: str = broker_url
        self._qos: int = qos

        if version == 3:
            # self._client = mqtt.Client(client_id=client_id,
            #                            transport=transport,
            #                            protocol=mqtt.MQTTv311,
            #                            clean_session=True)
            client = MQTTClient(client_id)
            token = os.environ.get('FLESPI_TOKEN')
            client.set_auth_credentials(token, password=password)
            self.version = MQTTv311
            self._client = MQTTClient(client_id)

        if version == 5:
            # self._client = mqtt.Client(client_id=client_id,
            #                            transport=transport,
            #                            protocol=mqtt.MQTTv5)
            self.version = MQTTv50
            self._client = MQTTClient(client_id)
        else:
            raise Exception("Invalid MQTT version!")

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish
        self._client.on_subscribe = self._on_subscribe
        # self._client.tls_set(),
        self._client.set_auth_credentials(username=username, password=password)
        # self._client.username_pw_set(username, password)

        self.topic = "TOPIC"
        self._connected: bool = False
        self._unacked_publish = set()
        # self._client.user_data_set(self._unacked_publish)
        self.tasks = []
        self.task = asyncio.create_task(self.work())
        self.sleep_time = 1
        self.queue = asyncio.Queue(maxsize=256)
        self.msg_for_send = []
        self.n = 0

    def start(self):
        loop = asyncio.get_running_loop()
        loop.run_until_complete(self.task)

    async def work(self):
        while True:
            try:
                self.n += 1
                print(f"work, {self.queue.empty()}")
                if not self.queue.empty():
                    if not self._connected:
                        await self.connect(host=self._broker_url,
                                           port=self._port,
                                           username=self._username,
                                           password=self._password)

                    topic, msg = await self.queue.get()
                    await self.publish(topic, msg)
                    # self.queue.task_done()

                    if self._connected\
                            and self.queue.empty():
                        await self.disconnect()

            except Exception as e:
                print(f"Mqtt Exception: {e}")

            await asyncio.sleep(self.sleep_time)

    def _on_connect(self, client, flags, rc, properties):
        """
        Callback function for MQTT on_connect event.

        :param client: MQTT client instance.
        :param flags: MQTT connection flags.
        :param rc: MQTT connection result code.
        :param properties: MQTT connection properties.
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

        self.subscribe(self.topic, qos=self._qos)

    async def _on_message(self, client, topic, payload, qos, properties):
        """
        Callback function for MQTT on_message event. This function is called when a PUBLISH message is received from
        the broker.

        :param client: MQTT client instance. This is the client that received the message.
        :type client: mqtt.Client

        :return: None
        """
        # Processing receive messages
        print(f"Receive message via MQTT {payload} on topic: {topic} ")
        return 0

    def _on_disconnect(self, client, packet, exc=None):
        """
        Callback function for MQTT on_disconnect event. This function is called when the client disconnects from the
        broker.

        :param client: MQTT client instance. This is the client that initiated the disconnect.
        :type client: mqtt.Client
        :return: None
        """

        self._connected = False
        print(f"Disconnected from MQTT broker.")

    def _on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        """
        Callback function for MQTT on_publish event. This function is called when a PUBLISH message is sent to the
        broker.

        Args:
            client (mqtt.Client): MQTT client instance. This is the client that sent the message.
            userdata (Any): User data. This is the user data that was set when creating the client instance.
            mid (int): Message ID. This is the ID of the message that was sent.
            reason_code (int, optional): The reason code for the publish. Defaults to None.
            properties (dict, optional): MQTT properties for the publish. Defaults to None.

        Returns:
            None
        """
        print(f"Reason code from broker: {reason_code}"
              f"\nMid: {mid}")
        pass

    def _on_subscribe(self, client, mid, qos, properties):
        """
        Callback function for MQTT on_subscribe event. This function is called when a SUBSCRIBE message is sent to
        the broker.

        Args:
            client (mqtt.Client): MQTT client instance. This is the client that sent the message.

        Returns:
            None
        """
        print(f"Subscribed: \n client: {client}"
              # f"userdata: {userdata}\n"
              f"mid: {mid}\n"
              # f"rc: {reason_code}\n"
              f"qos: {qos}\n"
              f"properties: {properties}")
        print(f"Subscribed back: \n client: {client}"
              # f"userdata: {userdata}\n"
              f"mid: {mid}\n"
              # f"rc: {reason_code}\n"
              f"properties: {properties}")

    async def connect(self, host, port, username, password):
        """
        Connect to MQTT broker.

        :param host: MQTT broker host.
        :param port: MQTT broker port.
        :param username: MQTT broker username.
        :param password: MQTT broker password.
        """
        try:
            print(f"MQTT connect: {self._broker_url}")

            # self._client.loop_start()
            # await self._client.connect(host=self._broker_url,
            #                      port=self._port,
            #                      keepalive=60)
            await self._client.connect(host=self._broker_url,
                                       port=self._port,
                                       keepalive=60,
                                       version=self.version,
                                       )

        except Exception as e:
            print(f"mqtt client: Exception: {e}")

    async def disconnect(self):
        """
        Disconnect from MQTT broker.
        """
        # self._client.loop_stop()
        await self._client.disconnect()

    async def publish(self, topic: str, payload: str | bytes, qos: int = 0, retain=None):
        """
        Publish a message to an MQTT topic.

        :param topic: MQTT topic.
        :param payload: MQTT message payload.
        :param qos: MQTT Quality of Service level.
        :param retain: Retain flag for the message.
        """
        # self._msg_info = self._client.publish(topic, payload, qos)
        self._client.publish(topic, payload, self._qos)
        print(f"Published to {topic}: {payload} with qos={self._qos}")
        # self._unacked_publish.add(self._msg_info)
        # self._msg_info.wait_for_publish(timeout=0.5)

    async def subscribe(self, topic: str, qos, callback):
        """
        Subscribe to an MQTT topic.

        :param qos:
        :param topic: MQTT topic.
        :param callback: Callback function to handle incoming messages.
        """
        await self._client.subscribe(topic, qos=self._qos)
        self._client.on_message = callback

    def unsubscribe(self, topic: str):
        """
        Unsubscribe from an MQTT topic.

        :param topic: MQTT topic.
        """
        self._client.unsubscribe(topic)

    async def save_data(self,
                        topic: str,
                        data: bytes | bytearray | int | float | str | None,
                        callback=None):
        """
        Save data to an MQTT topic.

        :param topic: MQTT topic.
        :param data: Data to be saved.
        :param callback: Callback function to handle the result.
        """
        try:
            # """Ukládání dat do zprávy."""
            # await self.publish(topic, payload=data, qos=self._qos, retain=None)
            await self.queue.put((topic, data))
            print(f"save_data {self.queue.qsize()}")
        except Exception as e:
            print(f"mqtt failed: {e}")

    def send_data(self, callback):
        """
        Send data to an MQTT topic.

        :param callback: Callback function to handle the result.
        """
        pass
