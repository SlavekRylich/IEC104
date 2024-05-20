# -*- coding: utf-8 -*-
# import paho.mqtt.client as mqtt
import asyncio

# from asyncio_mqtt import ProtocolVersion

from IDataSharing import IDataSharing
import aiomqtt as mqtt


# import paho.mqtt as mqtt


class MQTTProtocol_async(IDataSharing):
    """
    MQTTProtocol class for handling MQTT communication.
    """

    def __init__(self, client_id: str,
                 broker_url: str,
                 port: int,
                 username: str = None,
                 password: str = None,
                 version: int = None,
                 transport: str = "tcp",
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
        self.topic = "Doma/Pokoj1/Stul"
        self._username: str = username
        self._password: str = password
        self._broker_url: str = broker_url
        self._port: int = port
        self._qos: int = qos

        if version == 3:
            # self._client = mqtt.Client(client_id=client_id,
            #                            transport=transport,
            #                            protocol=mqtt.MQTTv311,
            #                            clean_session=True)
            self._client = mqtt.Client(
                hostname=self._broker_url,  # The only non-optional parameter
                port=self._port,
                username=username,
                password=password,
                clean_session=True,
            )
            self.transport = transport

        if version == 5:
            # self._client = mqtt.Client(client_id=client_id,
            #                            transport=transport,
            #                            protocol=mqtt.MQTTv5)
            self._client = mqtt.Client(
                hostname=self._broker_url,  # The only non-optional parameter
                port=self._port,
                username=username,
                password=password,
                identifier=client_id,
            )

            self.transport = transport
        else:
            raise Exception("Invalid MQTT version!")

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish
        self._client.on_subscribe = self._on_subscribe
        self._connected: bool = False
        self.task = asyncio.create_task(self.work())
        self.for_send = []
        self.reconnect_interval = 5
        self.run()

    def run(self):
        loop = asyncio.get_running_loop()
        asyncio.gather(self.task)

    async def work(self):
        while True:
            try:
                async with self._client as client:
                    self._connected = True
                    for topic, msg in self.for_send:
                        await self.publish(topic, msg)
                    await client.subscribe(self.topic)
                    async for message in client.messages:
                        self._on_message(client=client, message=message, userdata=None)

            except mqtt.MqttError as error:
                self._connected = False
                print(f'Error "{error}". Reconnecting in {self.reconnect_interval} seconds.')
                await asyncio.sleep(self.reconnect_interval)

    def _on_connect(self, client, userdata, flags, rc, properties):
        """
        Callback function for MQTT on_connect event.

        :param client: MQTT client instance.
        :param userdata: User data.
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

    def _on_message(self, client, userdata, message):
        """
        Callback function for MQTT on_message event. This function is called when a PUBLISH message is received from
        the broker.

        :param client: MQTT client instance. This is the client that received the message.
        :type client: mqtt.Client

        :param userdata: User data. This is the user data that was set when creating the client instance.
        :type userdata: Any

        :param message: MQTT message. This is the received PUBLISH message.
        :type message: mqtt.MQTTMessage

        :return: None
        """
        # Processing receive messages
        print(f"Receive message via MQTT {message}")
        pass

    def _on_disconnect(self, client, userdata, rc, properties):
        """
        Callback function for MQTT on_disconnect event. This function is called when the client disconnects from the
        broker.

        :param client: MQTT client instance. This is the client that initiated the disconnect.
        :type client: mqtt.Client

        :param userdata: User data. This is the user data that was set when creating the client instance.
        :type userdata: Any

        :param rc: The disconnection result code. 0 indicates a normal disconnection, 1 indicates that the client
        disconnected because it received a disconnect message from the broker, 2 indicates that the client is
        disconnecting due to a network error. :type rc: int

        :param properties: MQTT connection properties.
        :type properties: dict

        :return: None
        """
        if rc == 0:
            self._connected = False
            print("mqtt client clearly Disconnected")
        else:
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

    def _on_subscribe(self, client, userdata, mid, reason_code=None, properties=None):
        """
        Callback function for MQTT on_subscribe event. This function is called when a SUBSCRIBE message is sent to
        the broker.

        Args:
            client (mqtt.Client): MQTT client instance. This is the client that sent the message.
            userdata (Any): User data. This is the user data that was set when creating the client instance.
            mid (int): Message ID. This is the ID of the message that was sent.
            reason_code (int, optional): The reason code for the subscribe. Defaults to None.
            properties (dict, optional): MQTT properties for the subscribe. Defaults to None.

        Returns:
            None
        """
        print(f"Subscribed back: \n client: {client}"
              f"userdata: {userdata}\n"
              f"mid: {mid}\n"
              f"rc: {reason_code}\n"
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
            # await self._client.connect()

        except Exception as e:
            print(f"mqtt client: Exception: {e}")

    async def disconnect(self):
        """
        Disconnect from MQTT broker.
        """
        # self._client.loop_stop()
        # await self._client.disconnect()

    async def publish(self, topic: str, payload: str | bytes, qos: int = 0, retain=None):
        """
        Publish a message to an MQTT topic.

        :param topic: MQTT topic.
        :param payload: MQTT message payload.
        :param qos: MQTT Quality of Service level.
        :param retain: Retain flag for the message.
        """
        # self._msg_info = self._client.publish(topic, payload, qos)
        await self._client.publish(topic, payload, qos)
        print(f"Published to {topic}: {payload} with qos={qos}")
        # self._unacked_publish.add(self._msg_info)
        # self._msg_info.wait_for_publish(timeout=0.5)

    async def subscribe(self, topic, qos, callback):
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
            # await self.connect(host=self._broker_url,
            #                    port=self._port,
            #                    username=self._username,
            #                    password=self._password)
            # await self.publish(topic, payload=data, qos=self._qos, retain=None)
            self.for_send.append((topic, data))
        except Exception as e:
            print(f"mqtt failed: {e}")

    def send_data(self, callback):
        """
        Send data to an MQTT topic.

        :param callback: Callback function to handle the result.
        """
        pass
