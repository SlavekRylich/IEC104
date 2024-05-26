# -*- coding: utf-8 -*-
from datetime import datetime
import asyncio
import logging
from typing import Callable

from ASDU import ASDU
from FrameStatistics import FrameStatistics
from apci import APCI
from Frame import Frame
from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
from Packet_buffer import PacketBuffer
from Session import Session

# from MQTTProtocol_async_gmqtt import MQTTProtocol_async_gmqtt
# # from MQTTProtocol import MQTTProtocol
from MQTTProtocol import MQTTProtocol_async


class ClientManager:
    """
    Class represents the client and his features.
    """
    __id: int = 0

    def __init__(self, ip_addr: str,
                 port: int = None,
                 server_name: str = "",
                 mqtt_enabled: bool = False,
                 mqtt_broker_ip: str = "",
                 mqtt_broker_port: int = 1883,
                 mqtt_topic: str = "",
                 mqtt_version: int = None,
                 mqtt_transport: str = "",
                 mqtt_username: str = "",
                 mqtt_password: str = "",
                 mqtt_qos: int = 0,
                 callback_for_delete: Callable = None,
                 callback_on_message: Callable = None,
                 callback_on_disconnect: Callable = None,
                 flag_callbacks: Callable = False,
                 callback_only_for_client: Callable = None,
                 whoami: str = 'client'):
        """
        Constructor for QueueManager.

        Args:
            ip_addr (str): IP address.
            :rtype: object
            :param ip_addr:
            :param port: 
            :param server_name: 
            :param mqtt_broker_ip: 
            :param mqtt_broker_port: 
            :param mqtt_topic: 
            :param mqtt_version: 
            :param mqtt_transport: 
            :param mqtt_username: 
            :param mqtt_password: 
            :param mqtt_qos: 
            :param callback_for_delete: 
            :param callback_only_for_client: 
            :param whoami: 
        """
        # Instances of ClientManager
        ClientManager.__id += 1
        self.__id: int = ClientManager.__id

        # Session
        self.__sessions: list[Session] = []
        self.__VR: int = 0
        self.__VS: int = 0
        self.__ack: int = 0
        self.__ip: str = ip_addr
        self.__port: int = port

        # server x client
        self.__whoami = whoami

        # callbacks for Client app (client_app.py)
        self.__callback_only_for_client = callback_only_for_client
        # callback for check if is still connected any clients
        self.__callback_for_delete_self = callback_for_delete
        # callback for on_message
        self.__callback_on_message = callback_on_message
        # callback for disconnect
        self.__callback_on_disconnect = callback_on_disconnect
        # allow for 3rd party callbacks
        self.__flag_set_callbacks = flag_callbacks
        # Description of the client
        self.__server_name: str = server_name
        self.__name: str = "Client_" + str(self.__id)

        # flag for stop all tasks
        self.__flag_stop_tasks: bool = False

        # flag for delete queue because no it hasn't no session
        self.__flag_delete: bool = False

        # flag for first session is not yet 
        self.__flag_no_sessions: bool = False

        # flag for client_app for start communication
        self.__flag_start_sequence: bool = True

        # buffers
        self.__send_buffer: PacketBuffer = PacketBuffer()
        self.__recv_buffer: PacketBuffer = PacketBuffer()

        # central sleep time
        self.__async_time: float = 0.8

        # Tasks
        self.__tasks: list = []

        self.__loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

        # Setup for MQTT parameters
        if self.__whoami == "server":

            self.__mqtt_enabled = mqtt_enabled
            if mqtt_enabled:
                # MQTT client
                self.__mqtt_client_id: str = self.__ip + ':' + str(self.__port)
                self.__mqtt_broker_ip: str = mqtt_broker_ip
                self.__mqtt_broker_port: int = mqtt_broker_port
                self.__mqtt_topic: str = mqtt_topic
                self.__mqtt_version: int = mqtt_version
                self.__mqtt_transport: str = mqtt_transport
                self.__mqtt_username: str = mqtt_username
                self.__mqtt_password: str = mqtt_password
                self.__mqtt_qos: int = mqtt_qos
                # self.__mqtt_client = MQTTProtocol_async(self.__mqtt_client_id,
                #                                   self.__mqtt_broker_ip,
                #                                   self.__mqtt_broker_port,
                #                                   username=self.__mqtt_username,
                #                                   password=self.__mqtt_password,
                #                                   version=self.__mqtt_version,
                #                                   transport=self.__mqtt_transport,
                #                                   qos=self.__mqtt_qos)
                self.__mqtt_client = MQTTProtocol_async(self.__mqtt_client_id,
                                                        self.__mqtt_broker_ip,
                                                        self.__mqtt_broker_port,
                                                        username=self.__mqtt_username,
                                                        password=self.__mqtt_password,
                                                        version=self.__mqtt_version,
                                                        transport=self.__mqtt_transport,
                                                        qos=self.__mqtt_qos)
                # self.__mqtt_client.start(self.__loop)
        self.count = 0

        # statistics
        self.client_stats: FrameStatistics = FrameStatistics(self.ip)
        self.sessions_stats: dict[int, FrameStatistics] = {}

        # jak dostat data k odeslaní přes server (klienta)
        # přes nejaky API

        logging.debug(f"NEW INSTANCE CLIENTMANAGER ID: {self.__id}")

    async def start_mqtt(self) -> None:
        task = asyncio.ensure_future(self.__mqtt_client.start(self.__loop))
        self.__tasks.append(task)

    @property
    def flag_delete(self) -> bool:
        return self.__flag_delete

    @flag_delete.setter
    def flag_delete(self, value: bool) -> None:
        self.__flag_delete = value

    @property
    def flag_stop_tasks(self) -> bool:
        return self.__flag_stop_tasks

    @flag_stop_tasks.setter
    def flag_stop_tasks(self, value: bool) -> None:
        self.__flag_stop_tasks = value

    @property
    def send_buffer(self) -> PacketBuffer:
        return self.__send_buffer

    @property
    def recv_buffer(self) -> PacketBuffer:
        return self.__recv_buffer

    @property
    def ip(self) -> str:
        return self.__ip

    @property
    def id(self) -> int:
        return self.__id

    @property
    def flag_start_sequence(self) -> bool:
        if self.__flag_start_sequence:
            return True
        else:
            return False

    @flag_start_sequence.setter
    def flag_start_sequence(self, value: bool) -> None:
        logging.debug(f"flag_start_seq set to {value}")
        self.__flag_start_sequence = value

    @property
    def tasks(self) -> list:
        return self.__tasks

    def add_task(self, value: asyncio.create_task) -> None:
        self.__tasks.append(value)

    def get_client_stats(self) -> FrameStatistics:
        return self.client_stats

    def get_session_stats(self, id_num: int) -> FrameStatistics:
        return self.sessions_stats[id_num]

    def get_all_sessions_stat(self) -> dict:
        return self.sessions_stats

    async def send_frame(self, session: Session, frame: Frame) -> None:
        """
        Method to send frame and can catch statistics of sending frames.
        :rtype: object
        :param session:
        :param frame:
        """
        self.client_stats.update_send(frame)
        self.sessions_stats[session.port].update_send(frame)

        task = asyncio.ensure_future(session.send_frame(frame))
        self.__tasks.append(task)

    async def on_message_recv_or_timeout(self, session: Session, apdu: Frame = None) -> None:
        """
        This function is triggered when a new message is received or any timeout became.
        Redirects apdu for handle apdu and update state session
        or if apdu is None then it be update state session only.

        Args:
            session (Session): The session that received the message.
            apdu (Frame): The APDU frame that was received.

        Returns:
            None
            :param session:
            :param apdu:
            :rtype: object

        """
        logging.debug(f"Start on_message_recv_or_timeout")

        if apdu is not None:
            # update statistics
            self.client_stats.update_recv(apdu)
            self.sessions_stats[session.port].update_recv(apdu)

            # if apdu is Iformat save to buffer for acknowledgment
            if isinstance(apdu, IFormat):
                self.__recv_buffer.add_frame(apdu.ssn, apdu)

            # if it is server then handle own update states
            if self.__whoami == 'server':
                task = asyncio.ensure_future(self.update_state_machine_server(session, apdu))
                self.__tasks.append(task)
                task = asyncio.ensure_future(self.handle_apdu(session, apdu))
                self.__tasks.append(task)
                # await self.update_state_machine_server(session, apdu)
                # await self.handle_apdu(session, apdu)
            else:
                task = asyncio.ensure_future(self.update_state_machine_client(session, apdu))
                self.__tasks.append(task)
                task = asyncio.ensure_future(self.handle_apdu(session, apdu))
                self.__tasks.append(task)
                # await self.update_state_machine_client(session, apdu)
                # await self.handle_apdu(session, apdu)

        else:
            if self.__whoami == 'server':
                await self.update_state_machine_server(session)
            else:
                await self.update_state_machine_client(session)

        logging.debug(f"Finish on_message_recv_or_timeout")

    def delete_dead_session(self, session: Session = None) -> None:
        """
        Method for checking if any session still exists.
        If session has set flag for delete it will be deleted from list of sessions.
        If no session is found it will call delete_self method.

        :param session: The session object to be deleted.
        :return: None
        """
        self.__sessions.remove(session)
        logging.debug(f"deleted {session} from clientmanager")
        logging.info(f"{session.name} {session.ip}:{session.port} disconnected!")
        print(f"{session.name} {session.ip}:{session.port} disconnected!")

        if self.__flag_set_callbacks:
            self.__callback_on_disconnect(session)

        if len(self.__sessions) > 0:
            pass
        else:
            logging.debug(f"no sessions in clientManager, delete self")
            self.delete_self()

    def delete_self(self) -> None:
        """
        Method cancel all tasks associated, set flag for delete and call callback for server class instance.
        :rtype: object
        """
        # flag for stop coroutines
        self.flag_stop_tasks = True
        # flag for delete instance by ClientManager
        self.flag_delete = True
        self.__mqtt_client.stop = True
        for task in self.__tasks:
            try:
                task.cancel()

            except asyncio.CancelledError:
                # Zpracování zrušení tasků
                logging.debug(f"Cancel task succesfully!")

        # callback function in server class instance
        self.__callback_for_delete_self(self)
        del self

    async def callback_on_sent(self, session, data):
        """
        Method for callback function for 3rd party app.
        :rtype: object
        :param session:
        :param data:
        """
        if self.__flag_set_callbacks:
            if session.transmission_state == 'RUNNING':
                new_frame = self.generate_i_frame(data, session)
                task = asyncio.ensure_future(self.send_frame(session, new_frame))
                self.__tasks.append(task)

    def kill_session(self):
        for session in self.__sessions:
            session.delete_self()

    # for client and server
    async def handle_apdu(self, session: Session, apdu: Frame = None) -> None:
        """
        Method for handling the apdu by state diagram.
        :rtype: object
        :param session:
        :param apdu:
        """
        logging.debug(f"Starting handle_apdu, clientID: {self.id}, sessionID: {session.id}, apdu: {apdu}")
        # if isinstance(self._session, Session):

        actual_transmission_state = session.transmission_state

        # STATE 1
        if actual_transmission_state == 'STOPPED' or \
                actual_transmission_state == 'WAITING_RUNNING':

            if isinstance(apdu, UFormat):
                if apdu.type_int == APCI.TESTFR_ACT:
                    new_frame = self.generate_testdt_con()
                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                    self.__tasks.append(task)

        # STATE 2
        if actual_transmission_state == 'RUNNING':

            if isinstance(apdu, IFormat):

                if (apdu.ssn - self.__VR) > 1:

                    # chyba sekvence
                    # vyslat S-format s posledním self.VR

                    new_frame = self.generate_s_frame(session)
                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                    self.__tasks.append(task)
                    session.flag_session = 'ACTIVE_TERMINATION'
                    # raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")

                # correct I-format
                else:
                    self.incrementVR()
                    if apdu.rsn > self.ack:
                        self.ack = apdu.rsn
                        self.__send_buffer.clear_frames_less_than(self.__ack)

                    if self.__whoami == "server":
                        # handle apdu for on_message method
                        if self.__flag_set_callbacks:
                            task = asyncio.ensure_future(
                                self.__callback_on_message(session,
                                                           apdu,
                                                           apdu.data,
                                                           self.callback_on_sent))
                            self.__tasks.append(task)

                        if self.__mqtt_enabled:
                            o_apdu = ASDU(apdu.data)
                            topic = f"IEC104/{self.__name}/{session.name}/requests"
                            mqtt_data = {
                                "client": self.__name,
                                "session": session.name,
                                "request_code": o_apdu.type_id,
                            }

                            try:
                                # share payload with MQTT
                                task = asyncio.ensure_future(self.__mqtt_client.publish(
                                    topic=topic,
                                    payload=mqtt_data
                                ))
                                self.__tasks.append(task)

                            except Exception as e:
                                logging.error(f"Exception with publish in client manager: {e}")

                    # # odpověď stejnymi daty jen pro testovani
                    # new_apdu = self.generate_i_frame(apdu.data)
                    # self.__out_queue.to_send(new_apdu)

                if self.__recv_buffer.__len__() >= session.w:
                    new_frame = self.generate_s_frame(session)
                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                    self.__tasks.append(task)

            if isinstance(apdu, SFormat):
                if apdu.rsn > self.ack:
                    self.ack = apdu.rsn
                    self.__send_buffer.clear_frames_less_than(self.__ack)

            if isinstance(apdu, UFormat):
                if apdu.type_int == APCI.TESTFR_ACT:
                    new_frame = self.generate_testdt_con()
                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                    self.__tasks.append(task)

        # STATE 3
        if actual_transmission_state == 'WAITING_UNCONFIRMED' and \
                session.whoami == 'server':

            if isinstance(apdu, SFormat):
                if apdu.rsn > self.ack:
                    self.ack = apdu.rsn
                    self.__send_buffer.clear_frames_less_than(self.__ack)

            if isinstance(apdu, UFormat):

                if apdu.type_int == APCI.TESTFR_ACT:
                    new_frame = self.generate_testdt_con()
                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                    self.__tasks.append(task)

        # STATE FOR CLIENT APP
        if session.whoami == 'client' and \
                (actual_transmission_state == 'WAITING_UNCONFIRMED' or
                 actual_transmission_state == 'WAITING_STOPPED'):

            if isinstance(apdu, IFormat):
                if (apdu.ssn - self.__VR) > 1:
                    # bad sequence
                    # send S-format with last value of self.VR
                    new_frame = self.generate_s_frame(session)
                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                    self.__tasks.append(task)
                    session.flag_session = 'ACTIVE_TERMINATION'

                else:
                    self.incrementVR()
                    if apdu.rsn > self.ack:
                        self.ack = apdu.rsn
                        self.__send_buffer.clear_frames_less_than(self.__ack)
                # send S-format frame
                if self.__recv_buffer.__len__() >= session.w:
                    new_frame = self.generate_s_frame(session)
                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                    self.__tasks.append(task)

            if isinstance(apdu, SFormat):
                if apdu.rsn > self.ack:
                    self.ack = apdu.rsn
                    self.__send_buffer.clear_frames_less_than(self.__ack)

            if isinstance(apdu, UFormat):
                if apdu.type_int == APCI.TESTFR_ACT:
                    new_frame = self.generate_testdt_con()
                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                    self.__tasks.append(task)

        logging.debug(f"Finish async handle_apdu")

    def add_session(self, client_addr: str,
                    client_port: int,
                    reader: asyncio.StreamReader,
                    writer: asyncio.StreamWriter,
                    session_params: tuple,
                    callback_on_message_recv,
                    callback_timeouts_tuple: tuple,
                    whoami: str = 'server') -> Session:
        """
        Method for create new session instance of new client connection.
        :rtype: Session
        :param client_addr:
        :param client_port:
        :param reader:
        :param writer:
        :param session_params:
        :param callback_on_message_recv:
        :param callback_timeouts_tuple:
        :param whoami:
        :return: Session instance
        """
        session_number = self.get_number_of_sessions() + 1
        callback_for_del_session = self.delete_dead_session
        session = Session(session_number,
                          client_addr,
                          client_port,
                          reader, writer,
                          session_params,
                          callback_on_message_recv,
                          callback_timeouts_tuple,
                          callback_for_del_session,
                          self.send_buffer,
                          whoami=whoami)

        # create statistics object for session indexing by port
        self.sessions_stats[client_port] = FrameStatistics(client_addr, client_port)
        # add session instance in list of sessions
        self.__sessions.append(session)

        logging.info(f"Connection established with {client_addr}:{client_port} "
                     f"(Number of connections: {self.get_number_of_connected_sessions()})")

        return session

    def get_number_of_sessions(self) -> int:
        """
        Return number of session in list of sessions
        :return: int
        """
        return len(self.__sessions)

    def generate_i_frame(self, data: bytes, session: Session) -> IFormat:
        """
        Method generate a new I-format frame with the current counter states
        :rtype: IFormat
        :param data:
        :param session:
        :return: IFormat
        """
        session.update_timestamp_t2()
        new_i_format = IFormat(data, self.__VS, self.__VR)
        self.__recv_buffer.clear_frames_less_than(self.__ack)
        self.incrementVS()
        return new_i_format

    def generate_s_frame(self, session: Session) -> SFormat:
        """
        Method generate a new S-format frame with the current counter states
        :rtype: SFormat
        :param session:
        :return: SFormat
        """
        session.update_timestamp_t2()
        self.__recv_buffer.clear_frames_less_than(self.__VR)
        return SFormat(self.__VR)

    def get_number_of_connected_sessions(self) -> int:
        """
        Method returns number of session with CONNECTED state.
        :rtype: int
        :return: count
        """
        count = 0
        for session in self.__sessions:
            if session.connection_state == 'CONNECTED':
                count = count + 1
        return count

    @property
    def sessions(self) -> list[Session]:
        return self.__sessions

    def incrementVR(self) -> None:
        self.__VR = self.__VR + 1

    def incrementVS(self) -> None:
        self.__VS = self.__VS + 1

    @property
    def ack(self) -> int:
        return self.__ack

    @ack.setter
    def ack(self, ack: int) -> None:
        self.__ack = ack

    @property
    def VR(self) -> int:
        return self.__VR

    @property
    def VS(self) -> int:
        return self.__VS

    ################################################
    # GENERATE U-FRAME

    def generate_testdt_act(self) -> UFormat:
        return UFormat(APCI.TESTFR_ACT)

    def generate_testdt_con(self) -> UFormat:
        return UFormat(APCI.TESTFR_CON)

    def generate_startdt_act(self) -> UFormat:
        return UFormat(APCI.STARTDT_ACT)

    def generate_startdt_con(self) -> UFormat:
        return UFormat(APCI.STARTDT_CON)

    def generate_stopdt_act(self) -> UFormat:
        return UFormat(APCI.STOPDT_ACT)

    def generate_stopdt_con(self) -> UFormat:
        return UFormat(APCI.STOPDT_CON)

    async def update_state_machine_server(self, session: Session = None, fr: Frame = None) -> None:
        """
        Method for update state of session by receive frame or timeout.
        :param session:
        :param fr:
        """

        if not session.flag_stop_tasks:
            logging.debug(f"Starting update_state_machine_server with: {fr}")

            try:

                actual_transmission_state = session.transmission_state
                # set_connection_state()
                # 0 = DISCONNECTED
                # 1 = CONNECTED
                if session.connection_state == 'CONNECTED':

                    # correct format for conditions
                    if fr:
                        if isinstance(fr, UFormat):
                            frame = fr.type_int

                        else:
                            frame = fr.type_in_word  # S-format
                    else:
                        frame = 0

                    if session.flag_session != 'ACTIVE_TERMINATION':
                        # timeout t1
                        if not session.flag_timeout_t1:

                            # STATE 1
                            if actual_transmission_state == 'STOPPED':
                                if frame == APCI.STARTDT_ACT:
                                    # only one session can be in running state
                                    # -> send STOPDT act to other active sessions
                                    for other_session in self.__sessions:
                                        if other_session != session and \
                                                other_session.connection_state == 'CONNECTED' and \
                                                other_session.transmission_state != 'STOPPED':
                                            new_frame = self.generate_stopdt_act()
                                            task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                            self.__tasks.append(task)
                                            other_session.connection_state = 'DISCONNECTED'

                                    # ack with STARTDT con
                                    session.transmission_state = 'RUNNING'
                                    new_frame = self.generate_startdt_con()
                                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                    self.__tasks.append(task)

                                # S-format or I-format
                                if frame == 'S-format' or frame == 'I-format':
                                    session.flag_session = 'ACTIVE_TERMINATION'

                            # STATE 2
                            if actual_transmission_state == 'RUNNING':
                                # if frame is stopdt act and send queue is blank
                                if frame == APCI.STOPDT_ACT:
                                    # send STOPDT con
                                    if self.__recv_buffer.is_empty() and \
                                            self.__send_buffer.is_empty():
                                        new_frame = self.generate_stopdt_con()
                                        task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                        self.__tasks.append(task)
                                        session.transmission_state = 'STOPPED'

                                    else:  # if frame is STOPDT act and recv buffer is not blank
                                        if not self.__recv_buffer.is_empty():
                                            # ack all received_I-formats
                                            new_frame = self.generate_s_frame(session)
                                            task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                            self.__tasks.append(task)
                                        session.transmission_state = 'WAITING_UNCONFIRMED'

                            # STATE 3
                            if actual_transmission_state == 'WAITING_UNCONFIRMED':
                                if frame == 'S-format':
                                    if self.__send_buffer.is_empty() and \
                                            self.__recv_buffer.is_empty():
                                        # send STOPDT con
                                        new_frame = self.generate_stopdt_con()
                                        task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                        self.__tasks.append(task)
                                        session.transmission_state = 'STOPPED'

                                    if not self.__recv_buffer.is_empty():
                                        # ack all received_I-formats
                                        new_frame = self.generate_s_frame(session)
                                        task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                        self.__tasks.append(task)

                                #  I-format
                                if frame == 'I-format':
                                    session.flag_session = 'ACTIVE_TERMINATION'

                        else:
                            # reset flag_timeout_t1
                            session.flag_timeout_t1 = False
                            logging.debug(f"Timeout t1 is set to 0")
                            session.flag_session = 'ACTIVE_TERMINATION'

                        # default condition if ACTIVE_TERMINATION is set
                    if session.flag_session == 'ACTIVE_TERMINATION':
                        # unset ACTIVE_TERMINATION
                        session.flag_session = None
                        session.transmission_state = 'STOPPED'
                        session.connection_state = 'DISCONNECTED'

                        # delete session
                        session.delete_self()

                else:
                    session.transmission_state = 'STOPPED'
                    # delete session
                    session.delete_self()

                logging.debug(f"Finish async update_state_machine_server")

            except Exception as e:
                logging.error(f"Exception in update_state_machine_server: {e}")

    async def update_state_machine_client(self, session: Session = None, fr: Frame = None) -> None:
        """
        Method for update state of session by receive frame or timeout for client app.
        :param session:
        :param fr:
        """
        # while not session.flag_stop_tasks:
        if not session.flag_stop_tasks:

            try:
                logging.debug(f"Starting update_state_machine_client with {fr}")

                actual_transmission_state = session.transmission_state

                # get_connection_state()
                # 0 = DISCONNECTED
                # 1 = CONNECTED
                if session.connection_state == 'CONNECTED':

                    # correct format for next conditions
                    if fr:
                        if isinstance(fr, UFormat):
                            frame = fr.type_int

                        else:
                            frame = fr.type_in_word  # 'S-format'
                    else:
                        frame = 0

                    if session.flag_session != 'ACTIVE_TERMINATION':
                        # timeout t1
                        if not session.flag_timeout_t1:

                            # STATE 1
                            if actual_transmission_state == 'STOPPED':

                                # flag for start session is set
                                if session.flag_session == 'START_SESSION':
                                    # reset flag for start session
                                    session.flag_session = None
                                    # send START act
                                    new_frame = self.generate_startdt_act()
                                    task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                    self.__tasks.append(task)
                                    session.transmission_state = 'WAITING_RUNNING'

                                # t1_timeout or S-format or I-format
                                if frame == 'S-format' or frame == 'I-format':
                                    session.flag_session = 'ACTIVE_TERMINATION'

                            # STATE 2
                            if actual_transmission_state == 'WAITING_RUNNING':
                                if frame == APCI.STARTDT_CON:
                                    session.transmission_state = 'RUNNING'

                                # t1_timeout or S-format or I-format
                                if frame == 'S-format' or frame == 'I-format':
                                    session.flag_session = 'ACTIVE_TERMINATION'

                            # STATE 3
                            if actual_transmission_state == 'RUNNING':
                                # END RUNNING
                                if session.flag_session == 'STOP_SESSION':
                                    # reset flag for start session
                                    session.flag_session = None

                                    # To WAITING_STOPPED
                                    if self.__recv_buffer.is_empty() and \
                                            self.__send_buffer.is_empty():

                                        # send stopdt act
                                        new_frame = self.generate_stopdt_act()
                                        task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                        self.__tasks.append(task)
                                        # update state
                                        session.transmission_state = 'WAITING_STOPPED'

                                    else:
                                        # To WAITING_UNCONFIRMED
                                        if not self.__recv_buffer.is_empty():
                                            # ack all received_I-formats
                                            new_frame = self.generate_s_frame(session)
                                            task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                            self.__tasks.append(task)

                                        # send STOPDT act
                                        new_frame = self.generate_stopdt_act()
                                        task = asyncio.ensure_future(self.send_frame(session, new_frame))
                                        self.__tasks.append(task)

                                        # update state
                                        session.transmission_state = 'WAITING_UNCONFIRMED'

                            # STATE 4
                            if actual_transmission_state == 'WAITING_UNCONFIRMED':

                                if frame == APCI.STOPDT_CON:
                                    session.transmission_state = 'STOPPED'

                                if (frame == 'I-format' or frame == 'S-format') and \
                                        (self.__send_buffer.is_empty() and
                                         self.__recv_buffer.is_empty()):
                                    session.transmission_state = 'WAITING_STOPPED'

                            # STATE 5
                            if actual_transmission_state == 'WAITING_STOPPED':
                                if frame == APCI.STOPDT_CON:
                                    session.transmission_state = 'STOPPED'

                        else:
                            # reset flag_timeout_t1
                            session.flag_timeout_t1 = False
                            logging.debug(f"Timeout t1 is set to 0")
                            session.flag_session = 'ACTIVE_TERMINATION'

                    if session.flag_session == 'ACTIVE_TERMINATION':
                        # unset ACTIVE_TERMINATION
                        session.flag_session = None
                        session.transmission_state = 'STOPPED'
                        session.connection_state = 'DISCONNECTED'

                        session.delete_self()

                else:
                    session.delete_self()

                logging.debug(f"Finish async update_state_machine_client")

            except Exception as e:
                logging.error(f"Exception in update_state_machine_client: {e}")

    async def handle_timeout_t0(self, session: Session = None) -> None:
        """
        Method for handling timeout.
        :param session:
        """
        logging.debug(f"Timer t0 timed_out - {session}")
        logging.debug(f'Client {session.ip}:{session.port} timed out and disconnected')
        session.flag_session = 'ACTIVE_TERMINATION'
        session.delete_self()

    async def handle_timeout_t1(self, session: Session = None) -> None:
        """
        Method for handling timeout.
        :param session:
        """
        logging.debug(f"Timer t1 timed_out - {session}")
        session.flag_timeout_t1 = True
        task = asyncio.ensure_future(self.on_message_recv_or_timeout(session))
        self.__tasks.append(task)

    async def handle_timeout_t2(self, session: Session = None) -> None:
        """
        Method for handling timeout.
        :param session:
        """
        logging.debug(f"Timer t2 timed_out - {session}")
        if not self.__recv_buffer.is_empty():
            new_frame = self.generate_s_frame(session)
            task = asyncio.ensure_future(self.send_frame(session, new_frame))
            self.__tasks.append(task)

    async def handle_timeout_t3(self, session: Session = None) -> None:
        """
        Method for handling timeout.
        :param session:
        """
        logging.debug(f"Timer t3 timed_out - {session}")
        new_frame = self.generate_testdt_act()
        task = asyncio.ensure_future(self.send_frame(session, new_frame))
        self.__tasks.append(task)

    def __str__(self) -> str:
        return (f"Client: {self.ip},"
                f" ID: {self.id},"
                f" Num of sessions: {len(self.sessions)}")

    def __exit__(*exc_info):
        pass
