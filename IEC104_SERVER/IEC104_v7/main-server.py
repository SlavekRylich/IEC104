# -*- coding: utf-8 -*-

import gc
import logging
import asyncio

from FrameStatistics import FrameStatistics
from config_loader import ConfigLoader
from Session import Session
from ClientManager import ClientManager

# Nastavení úrovně logování
logging.basicConfig(
    filename='main-server.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Logování zprávy
logging.info("Toto je informační zpráva")
logging.warning("Toto je varovná zpráva")
logging.error("Toto je chybová zpráva")


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

        k = config_loader.config['server']['k']
        if k < 1 or k > 32767:
            raise Exception("Wrong value range for \'k\' variable!")

        w = config_loader.config['server']['w']
        if w > ((k * 2) / 3):
            if w < 1 or w > 32767:
                raise Exception("Wrong value range for \'w\' variable!")
            print(f"Warning! Use value range for "
                  "\'w\' less than 2/3 of \'k\'")

        t0 = config_loader.config['server']['t0']
        if t0 < 1 or t0 > 255:
            raise Exception("Wrong value range for \'t0\' variable!")

        t1 = config_loader.config['server']['t1']
        if t1 < 1 or t1 > 255:
            raise Exception("Wrong value range for \'t1\' variable!")

        t2 = config_loader.config['server']['t2']
        if t2 < 1 or t2 > 255:
            raise Exception("Wrong value range for \'t2\' variable!")

        t3 = config_loader.config['server']['t3']
        if t3 < 1 or t3 > 172800:
            raise Exception("Wrong value range for \'t3\' variable!")

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

    def send(self) -> None:
        """
        Send data to the clients.

        Args:
            None

        Returns:
            None

        Exceptions:
            None
        """
        pass

    def get_all_clients_stats(self) -> list | None:
        """
        Get all clients' statistics.

        Args:
            None

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

    async def listen(self) -> None:
        """
        Listen for incoming client connections.

        Args:
            None

        Returns:
            None

        Exceptions:
            None
        """
        print(f"Listen on {self.ip}:{self.port}")
        logging.info(f"Listen on {self.ip}:{self.port}")
        try:
            self._server = await asyncio.start_server(
                self.handle_client,
                self.ip,
                self.port,
            )

        except Exception as e:
            print(e)

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
        callback = self.check_alive_clients
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
                                                    callback_check_clients=callback,
                                                    callback_only_for_client=None,
                                                    whoami='server')

            self.clients[client_addr] = client_manager_instance

            print(f"Created new queue for client {client_addr}")
            logging.info(f"Created new queue for client {client_addr}")

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
            # Start the session
            await session.start()

        except Exception as e:
            print(f"Exception: {e}")
            logging.error(f"Exception: {e}")

    async def run(self) -> None:
        """
        Run the server.

        Args:
            None

        Returns:
            None

        Exceptions:
            None
        """

        self.__loop = asyncio.get_running_loop()
        pass
        # self.task_periodic_event_check = asyncio.create_task(self.periodic_event_check())

        # # while True:
        # try:
        #     await asyncio.gather(self.task_periodic_event_check,
        #                          *(task for task in self.tasks))
        #
        await self._server.serve_forever()
        #
        # except Exception as e:
        #     print(f"Exception {e}")
        # continue

        # await asyncio.sleep(self.async_time)

    def check_alive_clients(self) -> bool:
        """
        Check if any client in the list self.clients has a flag for deletion.
        If a client has the flag set, it is removed from the list.
        If no clients are left in the list, it returns False.
        If clients are still present, it returns True.

        Parameters:
        None

        Returns:
        bool: True if clients are still present, False otherwise.
        """

        # if there are any clients in the list
        if len(self.clients) > 0:
            count: int = 0
            # iterate over a copy of the clients list
            for client in list(self.clients.values()):
                # if the client has the flag for deletion
                if client.flag_delete:
                    # remove the client from the list
                    self.clients.pop(client.ip)
                    logging.debug(f"deleted {client} from server")
                    count += 1
                # if the client is None
                if client is None:
                    count += 1
                    logging.debug(f"deleted {client} because it's None")
            # if no clients were deleted
            if count == 0:
                logging.debug(f"last client was deleted")
                print(f"Waiting for connection...")
            print(count)
            # if there are still clients in the list
            if len(list(self.clients)) > 0:
                return True
            # if no clients are left in the list
            else:
                return False
        # if there are no clients in the list
        else:
            logging.debug(f"no clients on server")
            return False

    async def close(self) -> None:
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
        self.__loop.close()  # Close the asyncio event loop
        logging.info(f"Loop.close!")  # Log the closure of the event loop
        logging.shutdown()  # Shut down the logging system


# Main function
async def main() -> None:
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
    my_server = ServerIEC104()  # Initialize a new instance of the ServerIEC104 class
    await my_server.listen()  # Start listening for incoming client connections
    await my_server.run()  # Run the server


if __name__ == '__main__':

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass
    finally:
        pass
