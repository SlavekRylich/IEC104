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


class QueueManager:
    """
    Class for queue manager.
    """
    __id = 0
    __instances = []

    def __init__(self, ip, whoami='client'):
        """
        Constructor for QueueManager.

        Args:
            ip (str): IP address.
        """
        # Session
        self.__sessions = []
        self.__VR = 0
        self.__VS = 0
        self.__ack = 0
        self.__session = None
        self.__ip = ip

        self.__whoami = whoami

        # flag for stop all tasks
        self.__flag_stop_tasks = False

        # flag for delete queue because no it hasn't no session
        self.__flag_delete = False

        # flag for first session is not yet 
        self.__flag_no_sessions = False

        self.__flag_start_sequence = True

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
        self.__async_time = 0.8

        # Tasks
        self.__tasks = []

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

        self.data_list = [self.data2, self.data2]  # define static data

        QueueManager.__id += 1
        self.__id = QueueManager.__id
        QueueManager.__instances.append(self)
        print(f"NOVA INSTANCE QUEUE ID: {self.__id}")
        logging.debug(f"NOVA INSTANCE QUEUE ID: {self.__id}")

    async def start(self):
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
    def flag_delete(self):
        return self.__flag_delete

    @property
    def event_in(self, ):
        return self.__event_queue_in

    @property
    def event_out(self):
        return self.__shared_event_queue_out

    @property
    def in_queue(self):
        return self.__in_queue

    @property
    def out_queue(self):
        return self.__out_queue

    @property
    def send_buffer(self):
        return self.__send_buffer

    @property
    def recv_buffer(self):
        return self.__recv_buffer

    @property
    def id(self):
        return self.__id

    async def check_in_queue(self):
        while not self.__flag_stop_tasks:

            try:
                await self.__event_queue_in.wait()
                self.__event_queue_in.clear()
                print(f"Starting_check_in_queue")
                logging.debug(f"Starting_check_in_queue")

                if not self.__in_queue.is_Empty():
                    pass
                    # session, message = await self.__in_queue.get_message()

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

    async def on_handle_message(self, session: Session, apdu: Frame = None):
        """
        This function is triggered when a new message is received. Redirects apdu for handle apdu and update state session
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
    async def check_out_queue(self):
        while not self.__flag_stop_tasks:

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
    def ip(self):
        return self.__ip

    # remove session from sessions list if is not connected
    async def check_alive_sessions(self):
        while not self.__flag_stop_tasks:
            try:
                # if no sessions 
                if len(self.__sessions) == 0:

                    # if some session was but now is not
                    if self.__flag_no_sessions:
                        print(f"tady nastalo break")
                        logging.debug(f"tady nastalo break")
                        self.__flag_stop_tasks = True
                        break
                    else:
                        await asyncio.sleep(self.__async_time)
                        print(f"tady nastalo continue")
                        logging.debug(f"tady nastalo continue")
                        continue
                else:
                    # some session is connected        
                    self.__flag_no_sessions = True

                    print(f"tady je pripojeny 1 a vic klientu")
                    logging.debug(f"tady je pripojeny 1 a vic klientu")
                    # check if flag for delete session
                    for sess in self.__sessions:
                        if sess.flag_delete:
                            print(f"v session je nastaven priznak na delete")
                            logging.debug(f"v session je nastaven priznak na delete")
                            self.__sessions.remove(sess)
                            del sess

                await asyncio.sleep(self.__async_time)

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

        self.delete_self()

    def delete_self(self):
        for task in self.__tasks:
            try:
                task.cancel()

            except asyncio.CancelledError:
                # Zpracování zrušení tasků
                print(f"Zrušení tasku proběhlo úspěšně!")
                logging.debug(f"Zrušení tasku proběhlo úspěšně!")

        self.__flag_delete = True

    # for client and server
    async def handle_apdu(self, session: Session, apdu: Frame = None):

        print(f"Starting handle_apdu, clientID: {self.id}, sessionID: {session.id}, apdu: {apdu}")
        logging.debug(f"Starting handle_apdu, clientID: {self.id}, sessionID: {session.id}, apdu: {apdu}")
        # if isinstance(self._session, Session):

        actual_transmission_state = session.transmission_state
        session_event = session.event_queue_out

        if actual_transmission_state == 'STOPPED' or \
                actual_transmission_state == 'WAITING_RUNNING':

            if isinstance(apdu, UFormat):
                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    # self.__out_queue.to_send((session, frame), session_event)
                    await session.send_frame(frame)

        if actual_transmission_state == 'RUNNING':

            if isinstance(apdu, IFormat):

                if (apdu.ssn - self.__VR) > 1:

                    # chyba sekvence
                    # vyslat S-format s posledním self.VR
                    frame = await self.generate_s_frame(session)
                    # self.__out_queue.to_send((session, frame), session_event)
                    await session.send_frame(frame)
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
                    frame = await self.generate_s_frame(session)
                    # self.__out_queue.to_send((session, frame), session_event)
                    await session.send_frame(frame)

            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                await self.__send_buffer.clear_frames_less_than(self.__ack)

            if isinstance(apdu, UFormat):
                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    # self.__out_queue.to_send((session, frame), session_event)
                    await session.send_frame(frame)

        if actual_transmission_state == 'WAITING_UNCONFIRMED' and \
                session.whoami == 'server':

            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                await self.__send_buffer.clear_frames_less_than(self.__ack)
                # self.clear_acked_send_queue()

            if isinstance(apdu, UFormat):

                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    # self.__out_queue.to_send((session, frame), session_event)
                    await session.send_frame(frame)

        if session.whoami == 'client' and \
                (actual_transmission_state == 'WAITING_UNCONFIRMED' or
                 actual_transmission_state == 'WAITING_STOPPED'):

            if isinstance(apdu, IFormat):

                if (apdu.ssn - self.__VR) > 1:
                    # chyba sekvence
                    # vyslat S-format s posledním self.VR
                    frame = await self.generate_s_frame(session)
                    # self.__out_queue.to_send((session, frame), session_event)
                    await session.send_frame(frame)
                    session.flag_session = 'ACTIVE_TERMINATION'
                    # raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")

                else:
                    self.incrementVR()
                    self.ack = apdu.rsn
                    await self.__send_buffer.clear_frames_less_than(self.__ack)

                if self.__recv_buffer.__len__() >= session.w:
                    frame = await self.generate_s_frame(session)
                    # self.__out_queue.to_send((session, frame), session_event)
                    await session.send_frame(frame)

            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                await self.__send_buffer.clear_frames_less_than(self.__ack)

            if isinstance(apdu, UFormat):

                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    # self.__out_queue.to_send((session, frame), session_event)
                    await session.send_frame(frame)

        print(f"Finish async handle_apdu")
        logging.debug(f"Finish async handle_apdu")

    async def handle_response_for_client(self, session: Session):
        while not self.__flag_stop_tasks:
            print(f"Starting async handle_response ")
            logging.debug(f"Starting async handle_response ")
            actual_transmission_state = session.transmission_state
            session_event = session.event_queue_out

            try:

                # STATE MACHINE
                if session.connection_state == 'CONNECTED':

                    # * STATE 1
                    if actual_transmission_state == 'STOPPED':

                        frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await session.send_frame(frame)
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

                        frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await session.send_frame(frame)
                            await asyncio.sleep(2.5)

                    # * STATE 3
                    if actual_transmission_state == 'RUNNING':

                        # for cyklus for send I frame with random data
                        for data in self.data_list:
                            # list of data
                            frame = self.generate_i_frame(data, session)
                            # self.__out_queue.to_send((session, frame), session_event)
                            await session.send_frame(frame)
                            await asyncio.sleep(1.5)

                        # check if response is ack with S format

                        if self.__recv_buffer.__len__() >= session.w:
                            frame = await self.generate_s_frame(session)
                            # self.__out_queue.to_send((session, frame), session_event)
                            await session.send_frame(frame)

                        # send testdt frame
                        frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await session.send_frame(frame)
                            await asyncio.sleep(2.5)

                        await asyncio.sleep(10)
                        # session.flag_session = 'STOP_SESSION'
                        # print(f"nastaven priznak 'STOP_SESSION'")

                    # * STATE 4
                    if actual_transmission_state == 'WAITING_UNCONFIRMED':
                        # do not send new I frame, but check if response are I,S or U formats
                        # send testdt frame
                        frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await session.send_frame(frame)
                            await asyncio.sleep(2.5)

                        # session.flag_session = 'STOP_SESSION'

                    # * STATE 5
                    if actual_transmission_state == 'WAITING_STOPPED':
                        # # do not send new I frame, but check if response are I,S or U formats
                        # send testdt frame
                        frame = self.generate_testdt_act()
                        for i in range(0, 2):
                            # self.__out_queue.to_send((session, frame), session_event)
                            await session.send_frame(frame)
                            await asyncio.sleep(2.5)

                        # check if response is stopdt con
                        # frame = self.generate_stopdt_con()
                        # self.__out_queue.to_send((session,frame), session_event)

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

    async def isResponse(self):
        while not self.__flag_stop_tasks:
            try:
                await asyncio.sleep(self.__async_time)
            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

    def add_session(self, session):
        self.__sessions.append(session)
        # self.__session = self.Select_active_session(session)

    def get_number_of_sessions(self):
        count = 0
        for item in self.__sessions:
            count = count + 1
        return count

    def generate_i_frame(self, data, session):
        session.update_timestamp_t2()
        new_i_format = IFormat(data, self.__VS, self.__VR)
        self.incrementVS()
        return new_i_format

    async def generate_s_frame(self, session):
        session.update_timestamp_t2()
        await self.__recv_buffer.clear_frames_less_than(self.__VR)
        return SFormat(self.__VR)

    def Select_active_session(self):
        # logika výběru aktivního spojení
        # zatím ponechám jedno a to to poslední

        # self.sessions = (ip, port, session)
        for session in self.__sessions:
            if session.connection_state == 'CONNECTED' and \
                    session.priority < 1:
                self.__session = session
                return self.__session

    def get_number_of_connected_sessions(self):
        count = 0
        for session in self.__sessions:
            if session.connection_state == 'CONNECTED':
                count = count + 1
        return count

    def get_connected_sessions(self):
        list_sessions = []
        for session in self.__sessions:
            if session.connection_state == 'CONNECTED':
                list_sessions.append(session)
        return list_sessions

    def del_session(self, sess):

        for session in self.__sessions:
            if session == sess:
                print(f"Remove by del_session: {session}")
                logging.debug(f"Remove by del_session: {session}")
                self.__sessions.remove(session)
                return True
        return False

    def get_running_sessions(self):
        for session in self.__sessions:
            if session.transmission_state == 'RUNNING':
                return session

    @property
    def sessions(self):
        return self.__sessions

    def incrementVR(self):
        self.__VR = self.__VR + 1

    def incrementVS(self):
        self.__VS = self.__VS + 1

    @property
    def ack(self):
        return self.__ack

    @ack.setter
    def ack(self, ack):
        self.__ack = ack

    @property
    def VR(self):
        return self.__VR

    @property
    def VS(self):
        return self.__VS

    ################################################
    # GENERATE U FRAME

    def generate_testdt_act(self):
        return UFormat(acpi.TESTFR_ACT)

    def generate_testdt_con(self):
        return UFormat(acpi.TESTFR_CON)

    def generate_startdt_act(self):
        return UFormat(acpi.STARTDT_ACT)

    def generate_startdt_con(self):
        return UFormat(acpi.STARTDT_CON)

    def generate_stopdt_act(self):
        return UFormat(acpi.STOPDT_ACT)

    def generate_stopdt_con(self):
        return UFormat(acpi.STOPDT_CON)

    async def update_state_machine_server(self, session: Session = None, fr: Frame = None):
        # while not self.__flag_stop_tasks:
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
                                await session.send_frame(new_frame)

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
                                    await session.send_frame(new_frame)
                                    # poslat STOPDT CON
                                    session.transmission_state = 'STOPPED'

                                else:  # if frame is stopdt act and send queue is not blank
                                    if not self.__recv_buffer.is_empty():
                                        # ack all received_I-formats
                                        new_frame = await self.generate_s_frame(session)
                                        # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                        await session.send_frame(new_frame)
                                    session.transmission_state = 'WAITING_UNCONFIRMED'

                        # * STATE 3
                        if actual_transmission_state == 'WAITING_UNCONFIRMED':

                            if frame == 'S-format':
                                if self.__send_buffer.is_empty() and \
                                        self.__recv_buffer.is_empty():
                                    # poslat STOPDT CON
                                    new_frame = self.generate_stopdt_con()
                                    # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                    await session.send_frame(new_frame)

                                    # change state to 'STOPPED'
                                    session.transmission_state = 'STOPPED'

                                if not self.__recv_buffer.is_empty():
                                    # ack all received_I-formats
                                    new_frame = await self.generate_s_frame(session)
                                    # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                    await session.send_frame(new_frame)

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

                        session.flag_stop_tasks = True
                        # self.queue.del_session(self)

                else:
                    pass

                print(f"{session}")

                await asyncio.sleep(self.__async_time)
                print(f"Finish async update_state_machine_server")
                logging.debug(f"Finish async update_state_machine_server")

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

        self.delete_self()

    async def update_state_machine_client(self, session: Session = None, fr: Frame = None):
        # while not session.__flag_stop_tasks:
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
                                await session.send_frame(new_frame)
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
                                    await session.send_frame(new_frame)
                                    # update state
                                    session.transmission_state = 'WAITING_STOPPED'

                                else:
                                    # To WAITING_UNCONFIRMED
                                    if not self.__recv_buffer.is_empty():
                                        # ack all received_I-formats
                                        new_frame = await self.generate_s_frame(session)
                                        # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                        await session.send_frame(new_frame)

                                    # send stopdt act
                                    new_frame = self.generate_stopdt_act()
                                    # self.__out_queue.to_send((self, new_frame), self.__event_queue_out)
                                    await session.send_frame(new_frame)

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

                        session.flag_stop_tasks = True
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

        # del self
        self.delete_self()

    async def handle_timeout_t0(self, session: Session = None):
        print(f"Timer t0 timed_out - {session}")
        logging.debug(f"Timer t0 timed_out - {session}")
        allow_event_signal = 1
        print(f'Client {session.ip}:{session.port} timed out and disconnected')
        logging.debug(f'Client {session.ip}:{session.port} timed out and disconnected')
        session.flag_session = 'ACTIVE_TERMINATION'

    async def handle_timeout_t1(self, session: Session = None):
        print(f"Timer t1 timed_out - {session}")
        logging.debug(f"Timer t1 timed_out - {session}")
        allow_event_signal = 1
        session.flag_timeout_t1 = 1
        print(f"Timeout t1 is set to 1")
        logging.debug(f"Timeout t1 is set to 1")
        # raise TimeoutError(f"Timeout pro t1")

    async def handle_timeout_t2(self, session: Session = None):
        print(f"Timer t2 timed_out - {session}")
        logging.debug(f"Timer t2 timed_out - {session}")
        allow_event_signal = 1
        if not self.__recv_buffer.is_empty():
            new_frame = await self.generate_s_frame(session)
            # self.__out_queue.to_send((self, resp), self.__event_queue_out)
            await session.send_frame(new_frame)

    async def handle_timeout_t3(self, session: Session = None):
        print(f"Timer t3 timed_out - {session}")
        logging.debug(f"Timer t3 timed_out - {session}")
        allow_event_signal = 1
        new_frame = self.generate_testdt_act()
        # self.__out_queue.to_send((self, frame), self.__event_queue_out)
        await session.send_frame(new_frame)

    def __str__(self):
        return (f"Client: {self.ip},"
                f" ID: {self.id},"
                f" Num of sessions: {len(self.sessions)}")

    def __enter__(self):
        pass

    def __exit__(*exc_info):
        pass
