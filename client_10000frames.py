# -*- coding: utf-8 -*-
import struct
import logging
import time
import asyncio

from ClientManager import ClientManager
from Config_loader import ConfigLoader
from Session import Session

# Nastavení úrovně logování
logging.basicConfig(
    filename='client_app_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class IEC104Client(object):
    def __init__(self, name: str = "Client"):
        self.stop = None
        self.__flag_set_callbacks = False
        self.__callback_on_message = None
        self.__callback_on_disconnect = None
        self.__callback_on_connect = None
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.task_handle_response: asyncio.Task | None = None
        self.task_check_alive_queue: asyncio.Task | None = None
        self.client_manager: ClientManager | None = None
        self.active_session: Session | None = None
        self.servers: dict = {}
        self.__event: asyncio.Event = asyncio.Event()

        self.__name: str = name
        self.loop: asyncio.BaseEventLoop | None = None
        self.no_overflow: int = 0
        self.async_time: float = 0.8

        self.__config_loader: ConfigLoader = ConfigLoader('./config_parameters.json')

        self.__config_test: ConfigLoader = ConfigLoader('./config_10000frames.json')
        self.__count_test_frames = self.__config_test.config['test']['count']
        self.__test_pause = self.__config_test.config['test']['pause']/1000     # to ms

        # MQTT config
        self.mqtt_enabled: bool = self.__config_loader.config['mqtt']['enabled']
        self.mqtt_broker_ip: str = self.__config_loader.config['mqtt']['mqtt_broker_ip']
        self.mqtt_broker_port: int = self.__config_loader.config['mqtt']['mqtt_broker_port']
        self.mqtt_username: str = self.__config_loader.config['mqtt']['mqtt_username']
        self.mqtt_password: str = self.__config_loader.config['mqtt']['mqtt_password']
        self.mqtt_qos: int = self.__config_loader.config['mqtt']['mqtt_qos']

        self.data2: bytes = struct.pack(f"{'B' * 10}",
                                        0x65,  # start byte
                                        0x01,  # Total Length pouze hlavička
                                        0x0A,  # 1. ridici pole
                                        0x00,  # 2. ridici pole
                                        0x0C,  # 3. ridici pole
                                        0x00,  # 4. ridici pole hlavička
                                        0x00,  # 1. ridici pole
                                        0x00,  # 2. ridici pole
                                        0x00,  # 3. ridici pole
                                        0x05,  # 3. ridici pole
                                        )
        self.data2 = (b'\x0B\x07\x03\x00\x0C\x00\x10\x30\x00\xBE\x09\x00\x11\x30'
                      b'\x00\x90\x09\x00\x0E\x30\x00\x75\x00\x00\x28\x30\x00\x25\x09\x00\x29\x30\x00\x75'
                      b'\x00\x00\x0F\x30\x00\x0F\x0A\x00\x2E\x30\x00\xAE\x05\x00')

        dotaz_cteni_102 = b'\x66\x01\x05\x00\x01\x00\x01\x00\x00'
        # hodnota ve floating point
        merena_teplota_13 = b'\x0D\x81\x05\x00\x01\x00\x01\x00\x00\x42\xF6\x00\x11\x30'
        # aktivace
        povel_aktivace_45 = b'\x2D\x01\x06\x00\x01\x00\x02\x00\x00\x01'
        # deaktivace
        povel_deaktivace_45 = b'\x2D\x01\x08\x00\x01\x00\x02\x00\x00\x01'

        povel_potvrzeni_aktivace_45 = b'\x2D\x01\x07\x00\x01\x00\x02\x00\x00\x01'
        povel_potvrzeni_deaktivace_45 = b'\x2D\x01\x09\x00\x01\x00\x02\x00\x00\x00'

        self.data2 = b'\x2D\x01\x08\x00\x01\x00\x02\x00\x00\x01'
        self.dotaz_cteni_102 = b'\x66\x01\x05\x00\x01\x00\x01\x00\x00'
        self.povel_aktivace_45 = b'\x2D\x01\x06\x00\x01\x00\x02\x00\x00\x01'
        self.povel_deaktivace_45 = b'\x2D\x01\x08\x00\x01\x00\x02\x00\x00\x00'

        self.data_list: list[bytes] = [self.data2, self.data2]  # define static data

        self.server_ip: str = self.__config_loader.config['server']['ip_address']
        self.server_port: int = self.__config_loader.config['server']['port']

        # load configuration parameters
        try:
            self.k, self.w, \
                self.timeout_t0, \
                self.timeout_t1, \
                self.timeout_t2, \
                self.timeout_t3 = self.load_session_params(self.__config_loader)

            self.session_params: tuple = (self.k,
                                          self.w,
                                          self.timeout_t0,
                                          self.timeout_t1,
                                          self.timeout_t2,
                                          self.timeout_t3)

        except Exception as e:
            logging.error(f"Exception in load config: {e}")

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

    async def new_session(self, ip: str, port_num: int):
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port_num),
                timeout=self.timeout_t0
            )

            client_address, client_port = self.writer.get_extra_info('sockname')
            logging.info(f"Connected to {client_address}:{client_port}"
                         f"<-->{self.server_ip}:{self.server_port}")
            print(f"Connected to {client_address}:{client_port}"
                  f"<-->{self.server_ip}:{self.server_port}")

            # callback functions for class session
            callback_on_message_recv = self.client_manager.on_message_recv_or_timeout
            callback_timeouts_tuple = (
                self.client_manager.handle_timeout_t0,
                self.client_manager.handle_timeout_t1,
                self.client_manager.handle_timeout_t2,
                self.client_manager.handle_timeout_t3)
            active_session = self.client_manager.add_session(self.server_ip,
                                                             self.server_port,
                                                             self.reader,
                                                             self.writer,
                                                             self.session_params,
                                                             callback_on_message_recv,
                                                             callback_timeouts_tuple,
                                                             whoami='client')

            return active_session

        except asyncio.TimeoutError:
            logging.error(f"{time.ctime()} - Error with start session: {self.active_session}")
            pass
        except Exception as e:
            logging.error(f"Exception with create new session: {e}")

    async def connect(self, ip, port_num):
        try:
            self.__loop = asyncio.get_running_loop()

            callback_for_delete = self.delete_dead_clients
            callback_only_for_client = self.handle_response_for_client
            self.client_manager = ClientManager(ip,
                                                port=None,
                                                parent_name=self.__name,
                                                mqtt_enabled=self.mqtt_enabled,
                                                mqtt_broker_ip=self.mqtt_broker_ip,
                                                mqtt_broker_port=self.mqtt_broker_port,
                                                mqtt_username=self.mqtt_username,
                                                mqtt_password=self.mqtt_password,
                                                mqtt_qos=self.mqtt_qos,
                                                callback_for_delete=self.check_alive_clients,
                                                callback_on_message=self.__callback_on_message,
                                                callback_on_disconnect=self.__callback_on_disconnect,
                                                flag_callbacks=self.__flag_set_callbacks,
                                                callback_only_for_client=callback_only_for_client,
                                                whoami='client')

            logging.debug(f"Initializing {self.server_ip}:{self.server_port}")

            # přidá novou session a zároveň vybere aktivní session
            self.active_session: Session = await self.new_session(ip, port_num)
            if self.active_session is None:
                raise Exception("Connection refuse!")

            if self.__flag_set_callbacks:
                self.__callback_on_connect(ip, port_num, rc=0)

            self.servers[ip] = self.client_manager

            # set start session flag
            self.active_session.flag_session = 'START_SESSION'

            # self.task_periodic_event_check = asyncio.create_task(
            #     self.periodic_event_check()
            # )

            self.task_handle_response = asyncio.create_task(
                # self.client_manager.handle_response_for_client(self.active_session)
                self.handle_response_for_client(self.active_session)
            )

            # self.task_check_alive_queue = asyncio.create_task(
            #     self.queue.check_alive_sessions(),
            # )
            # await asyncio.gather(self.task_periodic_event_check,
            #                      self.task_queue,
            #                      self.task_check_alive_queue)
            # #
            # await asyncio.gather(self.task_periodic_event_check)

            # await asyncio.sleep(self.async_time)
            task_session = asyncio.create_task(self.active_session.start())
            task_mqtt_in_clientmager = asyncio.create_task(self.client_manager.start_mqtt())

            if self.mqtt_enabled:
                await asyncio.gather(task_session, self.task_handle_response, task_mqtt_in_clientmager)
            # Start the session
            await asyncio.gather(task_session, self.task_handle_response)


        except Exception as e:
            # Wrong connection
            if self.__flag_set_callbacks:
                self.__callback_on_connect("", 0, rc=1)
            logging.error(f"Exception with run client app: {e}")

    def check_alive_clients(self, server: ClientManager = None) -> None:

        # if is any client in list self.clients, check his flag for delete and remove it
        self.servers.pop(server.ip)
        logging.debug(f"{server} deleted from server")
        if len(self.servers) > 0:
            pass
        else:
            pass

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
        self.servers.pop(client.ip)
        logging.debug(f"{client} deleted from server")
        # if there are any clients in the list
        if len(self.servers) > 0:
            pass
        # if there are no clients in the list
        else:
            pass

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
            logging.error(f"Callbacks not set")
        #
        # print(f"Listen on {self.ip}:{self.port}")
        # logging.info(f"Listen on {self.ip}:{self.port}")

        while self.stop:
            try:
                await asyncio.sleep(2)
                pass
                # self._server = await asyncio.start_server(
                #     self.handle_client,
                #     self.ip,
                #     self.port,
                # )
                # self.__loop = asyncio.get_running_loop()
                # await self._server.serve_forever()

            except Exception as e:
                logging.error(f"Exception with start asyncio server {e}")
            finally:
                pass

    async def handle_response_for_client(self, session: Session) -> None:
        while not self.client_manager.flag_stop_tasks:
            logging.debug(f"Starting async handle_response ")
            actual_transmission_state = session.transmission_state
            session_event = session.event_queue_out

            try:

                # STATE MACHINE
                if session.connection_state == 'CONNECTED':

                    # * STATE 1
                    if actual_transmission_state == 'STOPPED':

                        new_frame = self.client_manager.generate_testdt_act()
                        for i in range(0, self.__count_test_frames):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await self.client_manager.send_frame(session, new_frame)
                            await asyncio.sleep(self.__test_pause)


                        # send start act
                        if self.client_manager.flag_start_sequence:
                            session.flag_session = 'START_SESSION'
                            self.client_manager.flag_start_sequence = False

                    # * STATE 2
                    if actual_transmission_state == 'WAITING_RUNNING':
                        # else send testdt frame

                        new_frame = self.client_manager.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await self.client_manager.send_frame(session, new_frame)
                            await asyncio.sleep(2.5)

                    # * STATE 3
                    if actual_transmission_state == 'RUNNING':

                        new_frame = self.client_manager.generate_i_frame(self.dotaz_cteni_102, session)
                        # self.__out_queue.to_send((session, frame), session_event)
                        await self.client_manager.send_frame(session, new_frame)
                        await asyncio.sleep(5)

                        new_frame = self.client_manager.generate_i_frame(self.povel_aktivace_45, session)
                        # self.__out_queue.to_send((session, frame), session_event)
                        await self.client_manager.send_frame(session, new_frame)
                        await asyncio.sleep(5)

                        new_frame = self.client_manager.generate_i_frame(self.povel_deaktivace_45, session)
                        # self.__out_queue.to_send((session, frame), session_event)
                        await self.client_manager.send_frame(session, new_frame)
                        await asyncio.sleep(5)

                        # # for cyklus for send I frame with random data
                        # for data in self.data_list:
                        #     # list of data
                        #     new_frame = self.client_manager.generate_i_frame(data, session)
                        #     # self.__out_queue.to_send((session, frame), session_event)
                        #     await self.client_manager.send_frame(session, new_frame)
                        #     await asyncio.sleep(1.5)

                        # check if response is ack with S format

                        if self.client_manager.recv_buffer.__len__() >= session.w:
                            new_frame = self.client_manager.generate_s_frame(session)
                            # self.__out_queue.to_send((session, frame), session_event)
                            await self.client_manager.send_frame(session, new_frame)

                        # send testdt frame
                        new_frame = self.client_manager.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await self.client_manager.send_frame(session, new_frame)
                            await asyncio.sleep(2.5)

                        await asyncio.sleep(1)
                        # session.flag_session = 'STOP_SESSION'

                    # * STATE 4
                    if actual_transmission_state == 'WAITING_UNCONFIRMED':
                        # do not send new I frame, but check if response are I,S or U formats
                        # send testdt frame
                        new_frame = self.client_manager.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await self.client_manager.send_frame(session, new_frame)
                            await asyncio.sleep(2.5)

                        # session.flag_session = 'STOP_SESSION'

                    # * STATE 5
                    if actual_transmission_state == 'WAITING_STOPPED':
                        # # do not send new I frame, but check if response are I,S or U formats
                        # send testdt frame
                        new_frame = self.client_manager.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await self.client_manager.send_frame(session, new_frame)
                            await asyncio.sleep(2.5)

                        # check if response is stopdt con
                        # frame = self.generate_stopdt_con()
                        # self.__out_queue.to_send((session,frame), session_event)

            except Exception as e:
                logging.error(f"Exception in handle_response_for_client: {e}")

    def close(self):
        """
        Close the client.

        This function closes the server by setting the stop flag to True.

        Parameters:
        None

        Returns:
        None

        Raises:
        None
        """
        print(f"called close()")
        if self.loop:
            self.loop.close()
        # self.stop = True
        # self.client_manager.flag_stop_tasks = True


if __name__ == "__main__":

    my_client = IEC104Client()
    try:
        asyncio.run(my_client.connect(my_client.server_ip, my_client.server_port))
    except KeyboardInterrupt:
        pass
    finally:
        pass
