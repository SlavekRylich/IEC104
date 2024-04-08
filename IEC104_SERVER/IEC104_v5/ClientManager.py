import asyncio
import logging
import struct

import acpi
from Frame import Frame

from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
# from IncomingQueueManager import IncomingQueueManager
# from OutgoingQueueManager import OutgoingQueueManager
from Packet_buffer import PacketBuffer
from Session import Session


class ClientManager:
    """
    Class for queue manager.
    """
    __id: int = 0
    __instances: list = []

    def __init__(self, ip: str,
                 port: int = None,
                 callback_check_clients=None,
                 whoami='client'):
        """
        Constructor for QueueManager.

        Args:
            ip (str): IP address.
        """
        # Session
        self.__out_queue = None
        self.__in_queue = None
        self.__sessions: list['Session'] = []
        self.__VR: int = 0
        self.__VS: int = 0
        self.__ack: int = 0
        self.__session = None
        self.__ip: str = ip
        self.__port: int = port

        self.__callback_check_alive_clients = callback_check_clients

        self.__whoami: str = whoami

        # flag for stop all tasks
        self.__flag_stop_tasks: bool = False

        # flag for delete queue because no it hasn't no session
        self.__flag_delete: bool = False

        # flag for first session is not yet 
        self.__flag_no_sessions: bool = False

        self.__flag_start_sequence: bool = True

        # queues events
        self.__event_queue_in = asyncio.Event()
        self.__shared_event_queue_out = asyncio.Event()

        # queues 
        # self.__in_queue = IncomingQueueManager(self.__event_queue_in)
        # self.__out_queue = OutgoingQueueManager(self.__shared_event_queue_out)

        # buffers
        self.__send_buffer = PacketBuffer()
        self.__recv_buffer = PacketBuffer()

        # central sleep time
        self.__async_time: float = 0.8

        # Tasks
        self.__tasks: list = []

        # jak dostat data k odeslaní přes server (klienta)
        # přes nejaky API
        self.data2 = struct.pack(f"{'B' * 10}",
                                 0x65,
                                 0x01,
                                 0x0A,
                                 0x00,
                                 0x0C,
                                 0x00,
                                 0x00,
                                 0x00,
                                 0x00,
                                 0x05,
                                 )

        self.data_list: list = [self.data2, self.data2]  # define static data

        ClientManager.__id += 1
        self.__id: int = ClientManager.__id
        ClientManager.__instances.append(self)

        print(f"NOVA INSTANCE QUEUE ID: {self.__id}")
        logging.debug(f"NOVA INSTANCE QUEUE ID: {self.__id}")

    async def start(self) -> None:
        try:
            pass
            # self.__tasks.append(asyncio.create_task(self.check_in_queue()))
            # # self.__tasks.append(asyncio.create_task(self.check_out_queue()))
            # self.__tasks.append(asyncio.create_task(self.isResponse()))
            # self.__tasks.append(asyncio.create_task(self.check_alive_sessions()))

            # await asyncio.gather(*self.__tasks)
        except Exception as e:
            print(f"Exception {e}")
            logging.error(f"Exception {e}")

            # await asyncio.sleep(self.__async_time)    

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
    def event_in(self, ) -> asyncio.Event:
        return self.__event_queue_in

    @property
    def event_out(self) -> asyncio.Event:
        return self.__shared_event_queue_out

    @property
    def in_queue(self) -> asyncio.Queue:
        return self.__in_queue

    @property
    def out_queue(self) -> asyncio.Queue:
        return self.__out_queue

    @property
    def send_buffer(self) -> PacketBuffer:
        return self.__send_buffer

    @property
    def recv_buffer(self) -> PacketBuffer:
        return self.__recv_buffer

    @property
    def id(self) -> int:
        return self.__id

    @classmethod
    def remove_instance(cls, id_num: int = 0, instance: 'ClientManager' = None) -> bool:
        if instance:
            cls.__instances.remove(instance)
            return True
        else:
            return False

    async def check_in_queue(self) -> None:
        while not self.flag_stop_tasks:

            try:
                await self.__event_queue_in.wait()
                self.__event_queue_in.clear()
                print(f"Starting_check_in_queue")
                logging.debug(f"Starting_check_in_queue")

                if not self.__in_queue.is_Empty():
                    pass
                    session, message = await self.__in_queue.get_message()

                    if isinstance(message, IFormat):
                        self.__recv_buffer.add_frame(message.ssn, message)

                    if self.__whoami == 'server':
                        await self.handle_apdu(session, message)
                    else:
                        await self.handle_apdu(session, message)
                        await self.handle_response_for_client(session)

                    await asyncio.sleep(self.__async_time)
                    print(f"Finish_check_in_queue")
                    logging.debug(f"Finish_check_in_queue")

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

            session = None
            message = None

    async def on_message_receive(self, session: Session, apdu: Frame = None) -> None:
        """
        This function is triggered when a new message is received.
        Redirects apdu for handle apdu and update state session
        or if apdu is None then it be update state session only.

        Args:
            session (Session): The session that received the message.
            apdu (Frame): The APDU frame that was received.

        Returns:
            None

        """
        print(f"Start on_handle_message")
        logging.debug(f"Start on_handle_message")

        if apdu is not None:

            # if apdu is Iformat save to buffer for acknowledgment
            if isinstance(apdu, IFormat):
                self.__recv_buffer.add_frame(apdu.ssn, apdu)

            if self.__whoami == 'server':
                await self.update_state_machine_server(session, apdu)
                await self.handle_apdu(session, apdu)
            else:
                await self.update_state_machine_client(session, apdu)
                await self.handle_apdu(session, apdu)
                # await self.handle_response_for_client(session)

        else:
            if self.__whoami == 'server':
                await self.update_state_machine_server(session)
            else:
                await self.update_state_machine_client(session)
                # await self.handle_response_for_client(session)

        # await asyncio.sleep(self.__async_time)
        print(f"Finish on_handle_message")
        logging.debug(f"Finish on_handle_message")

    # is handled in session
    async def check_out_queue(self) -> None:
        while not self.flag_stop_tasks:

            try:
                print(f"Starting_check_out_queue")
                logging.debug(f"Starting_check_out_queue")
                if not self.__out_queue.is_Empty():
                    pass

                await asyncio.sleep(self.__async_time)
            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

            print(f"Finish_check_out_queue")
            logging.debug(f"Finish_check_out_queue")

    @property
    def ip(self) -> str:
        return self.__ip

    # remove session from sessions list if is not connected
    def check_alive_sessions(self) -> bool:
        # if any session in list self.__sessions check his flag for delete and remove it
        if len(self.__sessions) > 0:
            count: int = 0
            for session in self.__sessions:
                if session.flag_delete:
                    self.__sessions.remove(session)
                    logging.debug(f"deleted {session} from clientmanager")
                    count += 1
                if session is None:
                    count += 1
                    print(f"nastalo toto ? ")
                    logging.debug(f"deleted {session} because it's None")
            if count == 0:
                logging.debug(f"no session deleted from clientmanager")
            print(count)
            if len(self.__sessions) > 0:
                return True
            else:
                self.delete_self()
                return False
        else:
            logging.debug(f"no sessions in clientManager, delete self")
            self.delete_self()
            return False

    def delete_self(self) -> None:
        # flag for stop coroutines
        self.flag_stop_tasks = True
        # flag for delete instance by ClientManager
        self.flag_delete = True

        for task in self.__tasks:
            try:
                task.cancel()

            except asyncio.CancelledError:
                # Zpracování zrušení tasků
                print(f"Zrušení tasku proběhlo úspěšně!")
                logging.debug(f"Zrušení tasku proběhlo úspěšně!")

        logging.debug(f"pred smazanim clientmanager: {self}")
        ClientManager.remove_instance(instance=self)
        logging.debug(f"po smazani clientmanager: {self}")

        self.__callback_check_alive_clients()
        del self

    # for client and server
    async def handle_apdu(self, session: Session, apdu: Frame = None) -> None:

        print(f"Starting handle_apdu, clientID: {self.id}, sessionID: {session.id}, apdu: {apdu}")
        logging.debug(f"Starting handle_apdu, clientID: {self.id}, sessionID: {session.id}, apdu: {apdu}")
        # if isinstance(self._session, Session):

        actual_transmission_state = session.transmission_state
        session_event = session.event_queue_out

        if actual_transmission_state == 'STOPPED' or \
                actual_transmission_state == 'WAITING_RUNNING':

            if isinstance(apdu, UFormat):
                if apdu.type_int == acpi.TESTFR_ACT:
                    new_frame = self.generate_testdt_con()
                    # self.__out_queue.to_send((session, frame), session_event)
                    task = asyncio.ensure_future(session.send_frame(new_frame))
                    self.__tasks.append(task)

        if actual_transmission_state == 'RUNNING':

            if isinstance(apdu, IFormat):

                if (apdu.ssn - self.__VR) > 1:

                    # chyba sekvence
                    # vyslat S-format s posledním self.VR
                    new_frame = await self.generate_s_frame(session)
                    # self.__out_queue.to_send((session, frame), session_event)
                    task = asyncio.ensure_future(session.send_frame(new_frame))
                    self.__tasks.append(task)
                    session.flag_session = 'ACTIVE_TERMINATION'
                    # raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")

                else:
                    self.incrementVR()
                    self.ack = apdu.rsn
                    await self.__send_buffer.clear_frames_less_than(self.__ack)

                    # # odpověď stejnymi daty jen pro testovani 
                    # new_apdu = self.generate_i_frame(apdu.data)
                    # self.__out_queue.to_send(new_apdu)

                if self.__recv_buffer.__len__() >= session.w:
                    new_frame = await self.generate_s_frame(session)
                    # self.__out_queue.to_send((session, frame), session_event)
                    task = asyncio.ensure_future(session.send_frame(new_frame))
                    self.__tasks.append(task)

            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                await self.__send_buffer.clear_frames_less_than(self.__ack)

            if isinstance(apdu, UFormat):
                if apdu.type_int == acpi.TESTFR_ACT:
                    new_frame = self.generate_testdt_con()
                    # self.__out_queue.to_send((session, frame), session_event)
                    task = asyncio.ensure_future(session.send_frame(new_frame))
                    self.__tasks.append(task)

        if actual_transmission_state == 'WAITING_UNCONFIRMED' and \
                session.whoami == 'server':

            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                await self.__send_buffer.clear_frames_less_than(self.__ack)
                # self.clear_acked_send_queue()

            if isinstance(apdu, UFormat):

                if apdu.type_int == acpi.TESTFR_ACT:
                    new_frame = self.generate_testdt_con()
                    # self.__out_queue.to_send((session, frame), session_event)
                    task = asyncio.ensure_future(session.send_frame(new_frame))
                    self.__tasks.append(task)

        if session.whoami == 'client' and \
                (actual_transmission_state == 'WAITING_UNCONFIRMED' or
                 actual_transmission_state == 'WAITING_STOPPED'):

            if isinstance(apdu, IFormat):

                if (apdu.ssn - self.__VR) > 1:
                    # chyba sekvence
                    # vyslat S-format s posledním self.VR
                    new_frame = await self.generate_s_frame(session)
                    # self.__out_queue.to_send((session, frame), session_event)
                    task = asyncio.ensure_future(session.send_frame(new_frame))
                    self.__tasks.append(task)
                    session.flag_session = 'ACTIVE_TERMINATION'
                    # raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")

                else:
                    self.incrementVR()
                    self.ack = apdu.rsn
                    await self.__send_buffer.clear_frames_less_than(self.__ack)

                if self.__recv_buffer.__len__() >= session.w:
                    new_frame = await self.generate_s_frame(session)
                    # self.__out_queue.to_send((session, frame), session_event)
                    task = asyncio.ensure_future(session.send_frame(new_frame))
                    self.__tasks.append(task)

            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                await self.__send_buffer.clear_frames_less_than(self.__ack)

            if isinstance(apdu, UFormat):

                if apdu.type_int == acpi.TESTFR_ACT:
                    new_frame = self.generate_testdt_con()
                    # self.__out_queue.to_send((session, frame), session_event)
                    task = asyncio.ensure_future(session.send_frame(new_frame))
                    self.__tasks.append(task)

        print(f"Finish async handle_apdu")
        logging.debug(f"Finish async handle_apdu")

    async def handle_response_for_client(self, session: Session) -> None:
        while not self.flag_stop_tasks:
            print(f"Starting async handle_response ")
            logging.debug(f"Starting async handle_response ")
            actual_transmission_state = session.transmission_state
            session_event = session.event_queue_out

            try:

                # STATE MACHINE
                if session.connection_state == 'CONNECTED':

                    # * STATE 1
                    if actual_transmission_state == 'STOPPED':

                        new_frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            task = asyncio.ensure_future(session.send_frame(new_frame))
                            self.__tasks.append(task)
                            await asyncio.sleep(2.5)

                        # send start act
                        if self.__flag_start_sequence:
                            session.flag_session = 'START_SESSION'
                            self.__flag_start_sequence = False
                            print(f"flag_start_seq = False")
                            logging.debug(f"flag_start_seq = False")

                    # * STATE 2
                    if actual_transmission_state == 'WAITING_RUNNING':
                        # else send testdt frame

                        new_frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            task = asyncio.ensure_future(session.send_frame(new_frame))
                            self.__tasks.append(task)
                            await asyncio.sleep(2.5)

                    # * STATE 3
                    if actual_transmission_state == 'RUNNING':

                        # for cyklus for send I frame with random data
                        for data in self.data_list:
                            # list of data
                            new_frame = self.generate_i_frame(data, session)
                            # self.__out_queue.to_send((session, frame), session_event)
                            task = asyncio.ensure_future(session.send_frame(new_frame))
                            self.__tasks.append(task)
                            await asyncio.sleep(1.5)

                        # check if response is ack with S format

                        if self.__recv_buffer.__len__() >= session.w:
                            new_frame = await self.generate_s_frame(session)
                            # self.__out_queue.to_send((session, frame), session_event)
                            task = asyncio.ensure_future(session.send_frame(new_frame))
                            self.__tasks.append(task)

                        # send testdt frame
                        new_frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            task = asyncio.ensure_future(session.send_frame(new_frame))
                            self.__tasks.append(task)
                            await asyncio.sleep(2.5)

                        await asyncio.sleep(10)
                        # session.flag_session = 'STOP_SESSION'
                        # print(f"nastaven priznak 'STOP_SESSION'")

                    # * STATE 4
                    if actual_transmission_state == 'WAITING_UNCONFIRMED':
                        # do not send new I frame, but check if response are I,S or U formats
                        # send testdt frame
                        new_frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            task = asyncio.ensure_future(session.send_frame(new_frame))
                            self.__tasks.append(task)
                            await asyncio.sleep(2.5)

                        # session.flag_session = 'STOP_SESSION'

                    # * STATE 5
                    if actual_transmission_state == 'WAITING_STOPPED':
                        # # do not send new I frame, but check if response are I,S or U formats
                        # send testdt frame
                        new_frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            task = asyncio.ensure_future(session.send_frame(new_frame))
                            self.__tasks.append(task)
                            await asyncio.sleep(2.5)

                        # check if response is stopdt con
                        # frame = self.generate_stopdt_con()
                        # self.__out_queue.to_send((session,frame), session_event)

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

    async def is_response(self) -> None:
        while not self.flag_stop_tasks:
            try:
                await asyncio.sleep(self.__async_time)
            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

    def add_session(self, session: Session) -> None:
        self.__sessions.append(session)
        # self.__session = self.Select_active_session(session)

    def get_number_of_sessions(self) -> int:
        return len(self.__sessions)

    def generate_i_frame(self, data: bytes, session: Session) -> IFormat:
        session.update_timestamp_t2()
        new_i_format = IFormat(data, self.__VS, self.__VR)
        self.incrementVS()
        return new_i_format

    async def generate_s_frame(self, session: Session) -> SFormat:
        session.update_timestamp_t2()
        await self.__recv_buffer.clear_frames_less_than(self.__VR)
        return SFormat(self.__VR)

    def Select_active_session(self) -> Session:
        # logika výběru aktivního spojení
        # zatím ponechám jedno a to to poslední

        # self.sessions = (ip, port, session)
        for session in self.__sessions:
            if session.connection_state == 'CONNECTED' and \
                    session.priority < 1:
                self.__session = session
                return self.__session

    def get_number_of_connected_sessions(self) -> int:
        count = 0
        for session in self.__sessions:
            if session.connection_state == 'CONNECTED':
                count = count + 1
        return count

    def get_connected_sessions(self) -> list[Session]:
        list_sessions = []
        for session in self.__sessions:
            if session.connection_state == 'CONNECTED':
                list_sessions.append(session)
        return list_sessions

    def del_session(self, sess: Session) -> bool:

        for session in self.__sessions:
            if session == sess:
                print(f"Remove by del_session: {session}")
                logging.debug(f"Remove by del_session: {session}")
                self.__sessions.remove(session)
                return True
        return False

    def get_running_sessions(self) -> Session:
        for session in self.__sessions:
            if session.transmission_state == 'RUNNING':
                return session

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
    # GENERATE U FRAME

    def generate_testdt_act(self) -> UFormat:
        return UFormat(acpi.TESTFR_ACT)

    def generate_testdt_con(self) -> UFormat:
        return UFormat(acpi.TESTFR_CON)

    def generate_startdt_act(self) -> UFormat:
        return UFormat(acpi.STARTDT_ACT)

    def generate_startdt_con(self) -> UFormat:
        return UFormat(acpi.STARTDT_CON)

    def generate_stopdt_act(self) -> UFormat:
        return UFormat(acpi.STOPDT_ACT)

    def generate_stopdt_con(self) -> UFormat:
        return UFormat(acpi.STOPDT_CON)

    async def update_state_machine_server(self, session: Session = None, fr: Frame = None) -> None:
        # while not self.flag_stop_tasks:
        if not session.flag_stop_tasks:
            # wait for allow
            # await self.__event_update.wait()
            # self.__event_update.clear()
            print(f"Starting update_state_machine_server with: {fr}")
            logging.debug(f"Starting update_state_machine_server with: {fr}")

            try:

                actual_transmission_state = session.transmission_state
                # set_connection_state()
                # 0 = DISCONNECTED
                # 1 = CONNECTED
                if session.connection_state == 'CONNECTED':

                    # get_connection_state()
                    # 0 = STOPPED
                    # 1= WAITING_RUNNING
                    # 2 = RUNNING
                    # 3 = WAITING_UNCONFIRMED
                    # 4 = WAITING_STOPPED

                    # if not self.__local_queue.empty():
                    #     fr = await self.__local_queue.get()
                    #     print(f"použit z lokalni fronty pro update: {fr}")

                    # correct format for conditions
                    if fr:
                        if isinstance(fr, UFormat):
                            frame = fr.type_int

                        else:
                            frame = fr.type_in_word  # S-format
                    else:
                        frame = 0

                    # timeout t1
                    if not session.flag_timeout_t1:

                        # * STATE 1
                        if actual_transmission_state == 'STOPPED':

                            if frame == acpi.STARTDT_ACT:
                                session.transmission_state = 'RUNNING'
                                new_frame = self.generate_startdt_con()
                                # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                task = asyncio.ensure_future(session.send_frame(new_frame))
                                self.__tasks.append(task)

                            # S-format or I-format
                            if frame == 'S-format' or frame == 'I-format':
                                session.flag_session = 'ACTIVE_TERMINATION'

                        # * STATE 2
                        if actual_transmission_state == 'RUNNING':

                            # if frame is stopdt act and send queue is blank
                            if frame == acpi.STOPDT_ACT:

                                if self.__recv_buffer.is_empty() and \
                                        self.__send_buffer.is_empty():

                                    new_frame = self.generate_stopdt_con()
                                    # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                    task = asyncio.ensure_future(session.send_frame(new_frame))
                                    self.__tasks.append(task)
                                    # poslat STOPDT CON
                                    session.transmission_state = 'STOPPED'

                                else:  # if frame is stopdt act and send queue is not blank
                                    if not self.__recv_buffer.is_empty():
                                        # ack all received_I-formats
                                        new_frame = await self.generate_s_frame(session)
                                        # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                        task = asyncio.ensure_future(session.send_frame(new_frame))
                                        self.__tasks.append(task)
                                    session.transmission_state = 'WAITING_UNCONFIRMED'

                        # * STATE 3
                        if actual_transmission_state == 'WAITING_UNCONFIRMED':

                            if frame == 'S-format':
                                if self.__send_buffer.is_empty() and \
                                        self.__recv_buffer.is_empty():
                                    # poslat STOPDT CON
                                    new_frame = self.generate_stopdt_con()
                                    # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                    task = asyncio.ensure_future(session.send_frame(new_frame))
                                    self.__tasks.append(task)

                                    # change state to 'STOPPED'
                                    session.transmission_state = 'STOPPED'

                                if not self.__recv_buffer.is_empty():
                                    # ack all received_I-formats
                                    new_frame = await self.generate_s_frame(session)
                                    # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                    task = asyncio.ensure_future(session.send_frame(new_frame))
                                    self.__tasks.append(task)

                            #  I-format
                            if frame == 'I-format':
                                session.flag_session = 'ACTIVE_TERMINATION'

                    else:
                        # reset flag_timeout_t1
                        session.flag_timeout_t1 = 0
                        print(f"Timeout t1 is set to 0")
                        logging.debug(f"Timeout t1 is set to 0")
                        session.flag_session = 'ACTIVE_TERMINATION'

                        # default condition if ACTIVE_TERMINATION is set
                    if session.flag_session == 'ACTIVE_TERMINATION':
                        # unset ACTIVE_TERMINATION
                        session.flag_session = None

                        session.transmission_state = 'STOPPED'
                        session.connection_state = 'DISCONNECTED'

                        # zde vyvolat odstranění session
                        session.delete_self()
                        self.check_alive_sessions()

                else:
                    pass

                print(f"{session}")

                await asyncio.sleep(self.__async_time)
                print(f"Finish async update_state_machine_server")
                logging.debug(f"Finish async update_state_machine_server")

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

    async def update_state_machine_client(self, session: Session = None, fr: Frame = None) -> None:
        # while not session.flag_stop_tasks:
        if not session.flag_stop_tasks:

            # wait for allow
            # await self.__event_update.wait()
            # self.__event_update.clear()

            try:
                print(f"Starting update_state_machine_client with {fr}")
                logging.debug(f"Starting update_state_machine_client with {fr}")

                actual_transmission_state = session.transmission_state

                # get_connection_state()
                # 0 = DISCONNECTED
                # 1 = CONNECTED
                if session.connection_state == 'CONNECTED':

                    # get_connection_state()
                    # 0 = STOPPED
                    # 1 = WAITING_RUNNING
                    # 2 = RUNNING
                    # 3 = WAITING_UNCONFIRMED
                    # 4 = WAITING_STOPPED
                    #
                    # if not self.__local_queue.empty():
                    #     fr = await self.__local_queue.get()
                    #     print(f"použit z lokalni fronty pro update: {fr}")

                    # correct format for next conditions
                    if fr:
                        if isinstance(fr, UFormat):
                            frame = fr.type_int

                        else:
                            frame = fr.type_in_word  # 'S-format'
                    else:
                        frame = 0

                    # timeout t1
                    if not session.flag_timeout_t1:

                        # * STATE 1 -
                        if actual_transmission_state == 'STOPPED':

                            # flag for start session is set
                            if session.flag_session == 'START_SESSION':
                                # reset flag for start session
                                session.flag_session = None
                                # send start act
                                new_frame = self.generate_startdt_act()
                                # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                task = asyncio.ensure_future(session.send_frame(new_frame))
                                self.__tasks.append(task)
                                # update state
                                session.transmission_state = 'WAITING_RUNNING'

                            # t1_timeout or S-format or I-format
                            if frame == 'S-format' or frame == 'I-format':
                                # aktivni ukonceni
                                session.flag_session = 'ACTIVE_TERMINATION'

                        # * STATE 2 -
                        if actual_transmission_state == 'WAITING_RUNNING':

                            if frame == acpi.STARTDT_CON:
                                session.transmission_state = 'RUNNING'

                            # t1_timeout or S-format or I-format
                            if frame == 'S-format' or frame == 'I-format':
                                # aktivni ukonceni
                                session.flag_session = 'ACTIVE_TERMINATION'

                        # * STATE 3 -
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
                                    # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                    task = asyncio.ensure_future(session.send_frame(new_frame))
                                    self.__tasks.append(task)
                                    # update state
                                    session.transmission_state = 'WAITING_STOPPED'

                                else:
                                    # To WAITING_UNCONFIRMED
                                    if not self.__recv_buffer.is_empty():
                                        # ack all received_I-formats
                                        new_frame = await self.generate_s_frame(session)
                                        # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                        task = asyncio.ensure_future(session.send_frame(new_frame))
                                        self.__tasks.append(task)

                                    # send stopdt act
                                    new_frame = self.generate_stopdt_act()
                                    # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                    task = asyncio.ensure_future(session.send_frame(new_frame))
                                    self.__tasks.append(task)

                                    # update state
                                    session.transmission_state = 'WAITING_UNCONFIRMED'

                        # * STATE 4
                        if actual_transmission_state == 'WAITING_UNCONFIRMED':

                            if frame == acpi.STOPDT_CON:
                                session.transmission_state = 'STOPPED'

                            if (frame == 'I-format' or frame == 'S-format') and \
                                    (self.__send_buffer.is_empty() and
                                     self.__recv_buffer.is_empty()):
                                session.transmission_state = 'WAITING_STOPPED'

                        # * STATE 5
                        if actual_transmission_state == 'WAITING_STOPPED':

                            if frame == acpi.STOPDT_CON:
                                session.transmission_state = 'STOPPED'

                    else:
                        # reset flag_timeout_t1
                        session.flag_timeout_t1 = 0
                        print(f"Timeout t1 is set to 0")
                        logging.debug(f"Timeout t1 is set to 0")
                        session.flag_session = 'ACTIVE_TERMINATION'

                        # default condition if ACTIVE_TERMINATION is set
                    if session.flag_session == 'ACTIVE_TERMINATION':
                        # unset ACTIVE_TERMINATION
                        session.flag_session = None
                        session.transmission_state = 'STOPPED'
                        session.connection_state = 'DISCONNECTED'

                        session.delete_self()
                        self.check_alive_sessions()
                else:
                    pass

                print(f"{session}")
                logging.info(f"{session}")

                await asyncio.sleep(self.__async_time)
                print(f"Finish async update_state_machine_client")
                logging.debug(f"Finish async update_state_machine_client")

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

    async def handle_timeout_t0(self, session: Session = None) -> None:
        print(f"Timer t0 timed_out - {session}")
        logging.debug(f"Timer t0 timed_out - {session}")
        print(f'Client {session.ip}:{session.port} timed out and disconnected')
        logging.debug(f'Client {session.ip}:{session.port} timed out and disconnected')
        session.flag_session = 'ACTIVE_TERMINATION'

    async def handle_timeout_t1(self, session: Session = None) -> None:
        print(f"Timer t1 timed_out - {session}")
        logging.debug(f"Timer t1 timed_out - {session}")
        session.flag_timeout_t1 = 1
        asyncio.ensure_future(self.on_message_receive(session))

        print(f"Timeout t1 is set to 1")
        logging.debug(f"Timeout t1 is set to 1")
        # raise TimeoutError(f"Timeout pro t1")

    async def handle_timeout_t2(self, session: Session = None) -> None:
        print(f"Timer t2 timed_out - {session}")
        logging.debug(f"Timer t2 timed_out - {session}")
        if not self.__recv_buffer.is_empty():
            new_frame = await self.generate_s_frame(session)
            # self.__out_queue.to_send((self, resp), self.__event_queue_out)
            task = asyncio.ensure_future(session.send_frame(new_frame))
            self.__tasks.append(task)

    async def handle_timeout_t3(self, session: Session = None) -> None:
        print(f"Timer t3 timed_out - {session}")
        logging.debug(f"Timer t3 timed_out - {session}")
        new_frame = self.generate_testdt_act()
        # self.__out_queue.to_send((self, frame), self.__event_queue_out)
        task = asyncio.ensure_future(session.send_frame(new_frame))
        self.__tasks.append(task)

    def __str__(self) -> str:
        return (f"Client: {self.ip},"
                f" ID: {self.id},"
                f" Num of sessions: {len(self.sessions)}")

    def __enter__(self) -> None:
        pass

    def __exit__(*exc_info):
        pass
