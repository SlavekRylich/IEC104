# -*- coding: utf-8 -*-
import asyncio
import json
import logging

import aiomqtt as mqtt


# import paho.mqtt as mqtt


class MQTTProtocol:
    """
    MQTTProtocol class for handling MQTT communication.
    """

    def __init__(self, client_id: str,
                 broker_url: str,
                 port: int,
                 username: str = None,
                 password: str = None,
                 qos: int = 0
                 ):
        """
        Initialize MQTTProtocol instance.

        :param client_id: MQTT client ID.
        :param broker_url: MQTT broker URL.
        :param port: MQTT broker port.
        :param username: MQTT broker username.
        :param password: MQTT broker password.
        :param qos: MQTT Quality of Service level.
        """

        # self._msg_info: mqtt.MQTTMessage | None = None
        self.task = None
        self.topic = ""
        self._username: str = username
        self._password: str = password
        self._broker_url: str = broker_url
        self._port: int = port
        self._qos: int = qos

        self.__client = mqtt.Client(
            hostname=self._broker_url,  # The only non-optional parameter
            port=self._port,
            username=username,
            password=password,
            identifier=client_id,
        )

        self.__client.on_connect = self._on_connect
        self.__client.on_message = self._on_message
        self.__client.on_disconnect = self._on_disconnect
        self.__client.on_publish = self._on_publish
        self.__client.on_subscribe = self._on_subscribe
        self._connected: bool = False
        self.for_send = []
        self.reconnect_interval = 5

        self.stop = False

    async def start(self, loop: asyncio.AbstractEventLoop):
        task = asyncio.ensure_future(self.run())
        await asyncio.gather(task)

    async def run(self):
        """
        Run MQTTProtocol instance.
        """
        logging.debug(f"Start communicate with MQTT broker: {self._broker_url}")

        while not self.stop:
            try:
                async with self.__client as client:
                    self._connected = True
                    for topic, data in self.for_send:
                        await self.publish(topic, payload=data, qos=self._qos, retain=None)
                    await client.subscribe(self.topic)
                    async for message in client.messages:
                        self._on_message(client=client, message=message, userdata=None)

            except mqtt.MqttError as error:
                self._connected = False
                logging.error(f'Error "{error}". Reconnecting in {self.reconnect_interval} seconds.')
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
            logging.debug(f"Connected to MQTT Broker on {self._broker_url}:{self._port}")
        elif rc == 1:
            logging.debug(f"Connection refused – incorrect protocol version")
        elif rc == 2:
            logging.debug(f"Connection refused – invalid client identifier")
        elif rc == 3:
            logging.debug(f"Connection refused – server unavailable")
        elif rc == 4:
            logging.debug(f"Connection refused – bad username or password")
        elif rc == 5:
            logging.debug(f"Connection refused – not authorised")
        else:
            logging.error(f"Bad connection: {rc}")

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
        logging.debug(f"Receive message via MQTT {message}")
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
            logging.debug("mqtt client clearly Disconnected")
        else:
            logging.debug(f"Disconnected from MQTT broker.")

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
        logging.debug(f"Reason code from broker: {reason_code}"
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
        logging.debug(f"Subscribed back: \n client: {client}"
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
            logging.info(f"MQTT connect: {self._broker_url}")

        except Exception as e:
            logging.error(f"mqtt client: Exception: {e}")

    async def disconnect(self):
        """
        Disconnect from MQTT broker.
        """
        pass

    async def publish(self, topic: str, payload: dict, qos: int = 0, retain=None):
        """
        Publish a message to an MQTT topic.

        :param topic: MQTT topic.
        :param payload: MQTT message payload.
        :param qos: MQTT Quality of Service level.
        :param retain: Retain flag for the message.
        """
        # self._msg_info = self._client.publish(topic, payload, qos)
        message = json.dumps(payload)
        if self._connected:
            await self.__client.publish(topic, message, self._qos)
            logging.debug(f"Published to {topic}: {message} with qos={qos}")
        else:
            self.for_send.append((topic, payload))

    async def subscribe(self, topic, qos, callback):
        """
        Subscribe to an MQTT topic.

        :param qos:
        :param topic: MQTT topic.
        :param callback: Callback function to handle incoming messages.
        """
        await self.__client.subscribe(topic, qos=self._qos)
        self.__client.on_message = callback
