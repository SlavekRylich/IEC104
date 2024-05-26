# -*- coding: utf-8 -*-
import struct
import logging
import time
import asyncio

from ClientManager import ClientManager
from config_loader import ConfigLoader
from Session import Session

# Nastavení úrovně logování
logging.basicConfig(
    filename='client_app_test1.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Logování zprávy
logging.info("Toto je informační zpráva")
logging.warning("Toto je varovná zpráva")
logging.error("Toto je chybová zpráva")


# tento soubor slouží k testování stavu, kdy se vystřídají stavy, pošle 35 I-formátů
# poté se počká 0.8t1 timeoutu a zašle se STOPDT act, opět se počká 0,8x t1 timeoutu a znovu
# se zahájí přenos 35 I-formátů

class IEC104Client(object):
    def __init__(self, name: str = "Client"):
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.task_handle_response: asyncio.Task | None = None
        self.__loop: asyncio.BaseEventLoop | None = None
        self.task_check_alive_queue: asyncio.Task | None = None
        self.client_manager: ClientManager | None = None
        self.active_session: Session | None = None
        self.servers: dict = {}
        self.data: str = 'random data'
        self.data1 = 0x65 + \
                     0x01 + \
                     0x0A + \
                     0x00 + \
                     0x0C + \
                     0x00 + \
                     0x00 + \
                     0x00 + \
                     0x00 + \
                     0x05

        self.__event: asyncio.Event = asyncio.Event()

        self.__name: str = name
        self.loop: asyncio.BaseEventLoop | None = None
        self.no_overflow: int = 0
        self.async_time: float = 0.8

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

        self.data_list: list[bytes] = [self.data2, self.data2]  # define static data

        config_loader: ConfigLoader = ConfigLoader('../../config_parameters.json')

        self.server_ip: str = config_loader.config['server']['ip_address']
        self.server_port: int = config_loader.config['server']['port']

        # load configuration parameters
        try:
            self.k, self.w, \
                self.timeout_t0, \
                self.timeout_t1, \
                self.timeout_t2, \
                self.timeout_t3 = self.load_params(config_loader)

            self.session_params: tuple = (self.k,
                                          self.w,
                                          self.timeout_t0,
                                          self.timeout_t1,
                                          self.timeout_t2,
                                          self.timeout_t3)

        except Exception as e:
            print(e)

        # test's times
        self.async_time_0_8xt1: float = 0.8 * self.timeout_t1

    def load_params(self, config_loader: ConfigLoader):

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

    async def new_session(self, ip: str, port_num: int):
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port_num),
                timeout=self.timeout_t0
            )

            client_address, client_port = self.writer.get_extra_info('sockname')
            print(f"Navázáno {client_address}:{client_port}"
                  f"-->{self.server_ip}:{self.server_port}")
            logging.info(f"Navázáno {client_address}:{client_port}"
                         f"-->{self.server_ip}:{self.server_port}")

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
            print(f"{time.ctime()} - Nastala chyba: {self.active_session}")
            logging.error(f"{time.ctime()} - Nastala chyba: {self.active_session}")
            pass
        except Exception as e:
            print(e)
            logging.error(f"Exception {e}")

    async def run_client(self, ip, port_num):
        try:
            self.__loop = asyncio.get_running_loop()

            callback_only_for_client = self.handle_response_for_client
            self.client_manager = ClientManager(ip,
                                                port=None,
                                                callback_for_delete=self.check_alive_clients,
                                                mqtt_version=3,
                                                callback_only_for_client=callback_only_for_client,
                                                whoami='client')
            # self._in_queue = self.queue.in_queue
            # self._out_queue = self.queue.out_queue
            # self._send_buffer = self.queue.send_buffer
            # self._recv_buffer = self.queue.recv_buffer
            # self.task_queue = asyncio.create_task(self.queue.start())

            print(f"Vytáčím {self.server_ip}:{self.server_port}")
            logging.debug(f"Vytáčím {self.server_ip}:{self.server_port}")

            # přidá novou session a zároveň vybere aktivní session
            self.active_session: Session = await self.new_session(ip, port_num)
            if self.active_session is None:
                raise Exception("Connection refuse!")

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

            await self.active_session.start()
            await self.task_handle_response

        except Exception as e:
            print(f"Exception: {e}")
            logging.error(f"Exception: {e}")

    def check_alive_clients(self) -> bool:

        # if is any client in list self.clients, check his flag for delete and remove it
        if len(self.servers) > 0:
            count: int = 0
            for server in list(self.servers.values()):
                if server.flag_delete:
                    self.servers.pop(server.ip)
                    logging.debug(f"deleted {server} from server")
                    count += 1
                if server is None:
                    count += 1
                    print(f"nastalo toto ? ")
                    logging.debug(f"deleted {server} because it's None")
            if count == 0:
                logging.debug(f"last client was deleted")

            if len(list(self.servers)) > 0:
                return True
            else:
                return False
        else:
            logging.debug(f"no clients on server")
            return False

    async def periodic_event_check(self):
        while True:
            print(f"Starting async server periodic event check.")
            logging.debug(f"Starting async server periodic event check.")
            try:
                # delete queue if no session is connected
                if len(self.servers) != 0:
                    if self.task_check_alive_queue.done():

                        for value in list(self.servers.values()):
                            if isinstance(value, ClientManager):
                                if value.flag_delete:
                                    del self.servers[value.ip]

                # UI se nebude volat tak často jako ostatní metody
                self.no_overflow = self.no_overflow + 1
                if self.no_overflow > 2:
                    self.no_overflow = 0

                    # await self.task_handle_response
                    print(f"no_overflow bezi")
                    logging.debug(f"no_overflow bezi")

                await asyncio.sleep(self.async_time)

            except TimeoutError as e:
                print(f"TimeoutError {e}")
                logging.error(f"TimeoutError {e}")
                pass

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

            await asyncio.sleep(self.async_time)

    async def handle_response_for_client(self, session: Session) -> None:
        while not self.client_manager.flag_stop_tasks:
            print(f"Starting async handle_response ")
            logging.debug(f"Starting async handle_response ")
            actual_transmission_state = session.transmission_state
            session_event = session.event_queue_out

            try:

                # STATE MACHINE
                if session.connection_state == 'CONNECTED':

                    # STATE 1
                    if actual_transmission_state == 'STOPPED':

                        new_frame = self.client_manager.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await self.client_manager.send_frame(session, new_frame)
                            await asyncio.sleep(2.5)

                        # send start act
                        if self.client_manager.flag_start_sequence:
                            session.flag_session = 'START_SESSION'
                            self.client_manager.flag_start_sequence = False
                            print(f"flag_start_seq = False")
                            logging.debug(f"flag_start_seq = False")

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

                        # for cyklus for send I frame with random data
                        for data in self.data_list:
                            # list of data
                            new_frame = self.client_manager.generate_i_frame(data, session)
                            # self.__out_queue.to_send((session, frame), session_event)
                            await self.client_manager.send_frame(session, new_frame)
                            await asyncio.sleep(1.5)

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

                        await asyncio.sleep(10)
                        # session.flag_session = 'STOP_SESSION'
                        # print(f"nastaven priznak 'STOP_SESSION'")

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
                print(f"Exception {e}")
                logging.error(f"Exception {e}")


if __name__ == "__main__":

    # host = "192.168.1.142"
    # host = "192.168.1.136"
    host = "127.0.0.1"
    port = 2404

    client = IEC104Client()
    try:
        asyncio.run(client.run_client(host, port))
    except KeyboardInterrupt:
        pass
    finally:
        pass
