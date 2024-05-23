# -*- coding: utf-8 -*-

import logging
import asyncio

from FrameStatistics import FrameStatistics
from config_loader import ConfigLoader
from Session import Session
from ClientManager import ClientManager

# Nastavení úrovně logování
logging.basicConfig(
    filename='server.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ServerIEC104:
    """
    Class for server IEC 104 protocol.
    """

    def __init__(self, name: str = "Server"):
        """
        Constructor for server IEC 104 protocol.

        Args:
            name (str): The name of the server. Default is "Server".

        Returns:
            None

        Exceptions:
            None
        """
        self.__name: str = name
        self.__loop: asyncio.BaseEventLoop | None = None
        self.task_check_alive_queue: asyncio.Task | None = None
        self._server: asyncio.Server | None = None
        self.__config_loader: ConfigLoader = ConfigLoader('./config_parameters.json')

        # ip config
        self.ip: str = self.__config_loader.config['server']['ip_address']
        self.port: int = self.__config_loader.config['server']['port']

        # MQTT config
        self.mqtt_broker_ip: str = self.__config_loader.config['mqtt']['mqtt_broker_ip']
        self.mqtt_broker_port: int = self.__config_loader.config['mqtt']['mqtt_broker_port']
        self.mqtt_topic: str = self.__config_loader.config['mqtt']['mqtt_topic']
        self.mqtt_version: int = self.__config_loader.config['mqtt']['mqtt_version']
        self.mqtt_transport: str = self.__config_loader.config['mqtt']['mqtt_transport']
        self.mqtt_username: str = self.__config_loader.config['mqtt']['mqtt_username']
        self.mqtt_password: str = self.__config_loader.config['mqtt']['mqtt_password']
        self.mqtt_qos: int = self.__config_loader.config['mqtt']['mqtt_qos']

        # tasks
        self.tasks: list[asyncio.Task] = []

        # clients - dictionary[ip_add, ClientManager]
        self.clients: dict[str, ClientManager] = {}

        # callbacks
        self.__callback_on_connect = None
        self.__callback_on_disconnect = None
        self.__callback_on_message = None
        self.__flag_set_callbacks = False

        # working var
        self.no_overflow: int = 0

        # central sleep time
        self.async_time: float = 0.5

        # load configuration parameters
        try:
            self.k, self.w, \
                self.timeout_t0, \
                self.timeout_t1, \
                self.timeout_t2, \
                self.timeout_t3 = self.load_session_params(self.__config_loader)

            # save parameters into tuple 
            self.config_parameters: tuple = (self.k,
                                             self.w,
                                             self.timeout_t0,
                                             self.timeout_t1,
                                             self.timeout_t2,
                                             self.timeout_t3)

        except Exception as e:
            print(e)
            self.close()

    def load_session_params(self, config_loader: ConfigLoader) -> tuple:
        """
        Load session parameters from the configuration loader.

        Args:
            config_loader (ConfigLoader): The configuration loader object.

        Returns:
            tuple: A tuple containing the loaded session parameters.

        Exceptions:
            Exception: If any of the session parameters are out of range.
        """

        k: int = config_loader.config['server']['k']
        if k < 1 or k > 32767:
            logging.critical("Wrong value range for \'k\' parameter!\n"
                             "Correct range is <1-32767>. ")
            raise Exception("Wrong value range for \'k\' parameter!\n"
                            "Correct range is <1-32767>. ")

        w: int = config_loader.config['server']['w']
        if w < 1 or w > 32767:
            logging.critical("Wrong value range for \'w\' parameter!\n"
                             "Correct range is <1-32767>. ")
            raise Exception("Wrong value range for \'w\' parameter!\n"
                            "Correct range is <1-32767>. ")
        if w > ((k * 2) / 3):
            logging.warning(f"Use value range for \'w\' less than 2/3 of \'k\'."
                            f"The application will not work properly!")

        t0 = config_loader.config['server']['t0']
        if t0 < 1 or t0 > 255:
            logging.critical("Wrong value range for \'t0\' parameter!\n"
                             "Correct range is <1-255> seconds. Minimal unit 1 sec. ")
            raise Exception("Wrong value range for \'t0\' parameter!\n"
                            "Correct range is <1-255> seconds. Minimal unit 1 sec. ")

        t1 = config_loader.config['server']['t1']
        if t1 < 1 or t1 > 255:
            logging.critical("Wrong value range for \'t1\' parameter!\n"
                             "Correct range is <1-255> seconds. Minimal unit 1 sec. ")
            raise Exception("Wrong value range for \'t1\' parameter!\n"
                            "Correct range is <1-255> seconds. Minimal unit 1 sec. ")

        t2 = config_loader.config['server']['t2']
        if t2 < 1 or t2 > 255:
            logging.critical("Wrong value range for \'t2\' parameter!\n"
                             "Correct range is <1-255> seconds. Minimal unit 1 sec. ")
            raise Exception("Wrong value range for \'t2\' parameter!\n"
                            "Correct range is <1-255> seconds. Minimal unit 1 sec. ")
        if t2 >= t1:
            logging.critical("Wrong value for \'t2\' parameter!\n"
                             "It must be t2 < t1!")
            raise Exception("Wrong value for \'t2\' parameter!\n"
                            "It must be t2 < t1!")

        t3 = config_loader.config['server']['t3']
        if t3 < 1 or t3 > 172800:
            logging.critical("Wrong value range for \'t3\' parameter!\n"
                             "Correct range is <1-172800> seconds. Minimal unit 1 sec. ")
            raise Exception("Wrong value range for \'t3\' parameter!\n"
                            "Correct range is <1-172800> seconds. Minimal unit 1 sec. ")

        return k, w, t0, t1, t2, t3

    @property
    def name(self):
        """
        Get the name of the server.

        Returns:
            str: The name of the server.
        """
        return self.__name

    @name.setter
    def name(self, value):
        """
        Set the name of the server.

        Args:
            value (str): The new name of the server.

        Returns:
            None

        Exceptions:
            None
        """
        self.__name = value

    @property
    def register_callback_on_connect(self):
        return self.__callback_on_connect

    @register_callback_on_connect.setter
    def register_callback_on_connect(self, func):
        self.__callback_on_connect = func

    @property
    def register_callback_on_disconnect(self):
        return self.__callback_on_disconnect

    @register_callback_on_disconnect.setter
    def register_callback_on_disconnect(self, func):
        self.__callback_on_disconnect = func

    @property
    def register_callback_on_message(self):
        return self.__callback_on_message

    @register_callback_on_message.setter
    def register_callback_on_message(self, func):
        self.__callback_on_message = func

    def get_all_clients_stats(self) -> list | None:
        """
        Get all clients' statistics.

        Args:

        Returns:
            list: A list of all clients' statistics.

        Exceptions:
            None
        """
        local_list: list[FrameStatistics] = []
        for client in self.clients.values():
            local_list.append(client.get_client_stats())
            for session_stats in client.get_all_sessions_stat():
                local_list.append(session_stats)

        if local_list.__sizeof__() > 0:
            return local_list
        return None

    async def handle_client(self, reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter) -> None:
        """
        Handle a new client connection.

        Args:
            reader (asyncio.StreamReader): The stream reader for the incoming data from the client.
            writer (asyncio.StreamWriter): The stream writer for sending data to the client.

        Returns:
            None

        Exceptions:
            None
        """
        client_addr, client_port = writer.get_extra_info('peername')
        """
        Get the IP address of the client that connected to the server.
        """
        callback_for_delete = self.delete_dead_clients
        if client_addr not in self.clients:
            client_manager_instance = ClientManager(client_addr,
                                                    port=self.port,
                                                    server_name=self.name,
                                                    mqtt_broker_ip=self.mqtt_broker_ip,
                                                    mqtt_broker_port=self.mqtt_broker_port,
                                                    mqtt_topic=self.mqtt_topic,
                                                    mqtt_version=self.mqtt_version,
                                                    mqtt_transport=self.mqtt_transport,
                                                    mqtt_username=self.mqtt_username,
                                                    mqtt_password=self.mqtt_password,
                                                    mqtt_qos=self.mqtt_qos,
                                                    callback_for_delete=callback_for_delete,
                                                    callback_on_message=self.__callback_on_message,
                                                    callback_on_disconnect=self.__callback_on_disconnect,
                                                    flag_callbacks=self.__flag_set_callbacks,
                                                    callback_only_for_client=None,
                                                    whoami='server')

            self.clients[client_addr] = client_manager_instance

            print(f"Established with new client: {client_addr}")
            logging.info(f"Established with new client: {client_addr}")

        client_manager_instance: ClientManager = self.clients[client_addr]

        # Get the functions to call for handling incoming APDU packets and timeout events
        callback_on_message_recv = client_manager_instance.on_message_recv_or_timeout
        callback_timeouts_tuple: tuple = (
            client_manager_instance.handle_timeout_t0,
            client_manager_instance.handle_timeout_t1,
            client_manager_instance.handle_timeout_t2,
            client_manager_instance.handle_timeout_t3,
        )

        # Create a new Session object for the client
        # Add the session to the queue
        session: Session = client_manager_instance.add_session(client_addr,
                                                               client_port,
                                                               reader,
                                                               writer,
                                                               self.config_parameters,
                                                               callback_on_message_recv,
                                                               callback_timeouts_tuple,
                                                               whoami='server')

        try:
            task = asyncio.create_task(session.start())

            # Success connect with client
            if self.__flag_set_callbacks:
                self.__callback_on_connect(client_addr, client_port, rc=0)
            # Start the session
            await task

        except Exception as e:
            # Wrong connection
            if self.__flag_set_callbacks:
                self.__callback_on_connect("", 0, rc=1)
            print(f"Exception: {e}")
            logging.error(f"Exception with start handle_messages(): {e}")

    def delete_dead_clients(self, client: ClientManager = None) -> None:
        """
        Check if any client in the list self.clients has a flag for deletion.
        If a client has the flag set, it is removed from the list.
        If no clients are left in the list, it returns False.
        If clients are still present, it returns True.

        Parameters:
        None

        Returns:
        None:
        """
        self.clients.pop(client.ip)
        logging.debug(f"{client} deleted from server")
        # if there are any clients in the list
        if len(self.clients) > 0:
            pass
        # if there are no clients in the list
        else:
            print(f"Listen on {self.ip}:{self.port}")
            logging.info(f"Listen on {self.ip}:{self.port}")

    def kill_clients(self):
        try:
            for client in self.clients.values():
                client.kill_session()
        except Exception as e:
            print(f"Exception with kill: {e}")
            logging.error(f"Exception with kill: {e}")

    def close(self) -> None:
        """
        Close the asyncio event loop and shutdown the logging system.

        This method should be called when the server is no longer needed to free up system resources.
        It closes the asyncio event loop and shuts down the logging system.

        Parameters:
        None

        Returns:
        None

        Raises:
        None
        """
        if self._server:
            self._server.close()
            self.kill_clients()
            logging.info(f"Stopping server.")  # Log the closure of the event loop
        if self.__loop:
            self.__loop.close()  # Close the asyncio event loop
            logging.info(f"Loop.close!")  # Log the closure of the event loop
        logging.shutdown()  # Shut down the logging system
        exit()

    # Main function
    async def start(self) -> None:
        """
        The main function of the server application.

        This function initializes a new instance of the ServerIEC104 class,
        starts listening for incoming client connections, and runs the server.

        Parameters:
        None

        Returns:
        None

        Raises:
        None
        """
        if self.__callback_on_connect and self.__callback_on_message and self.__callback_on_disconnect:
            self.__flag_set_callbacks = True

        else:
            print(f"Callback not set")
            logging.error(f"Callback not set")

        print(f"Listen on {self.ip}:{self.port}")
        logging.info(f"Listen on {self.ip}:{self.port}")
        try:
            self._server = await asyncio.start_server(
                self.handle_client,
                self.ip,
                self.port,
            )
            self.__loop = asyncio.get_running_loop()
            await self._server.serve_forever()

        except Exception as e:
            print(f"Exception {e}")
        finally:
            pass


if __name__ == '__main__':

    my_server = ServerIEC104()
    try:
        asyncio.run(my_server.start())
        print(f"az po tom")

    except KeyboardInterrupt:
        pass
    finally:
        pass
