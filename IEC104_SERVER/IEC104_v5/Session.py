import logging
import asyncio
import time
from typing import Any

import Packet_buffer
from Timer import Timer
from Frame import Frame
from Parser import Parser
from IFormat import IFormat
from State import ConnectionState, TransmissionState


# from IncomingQueueManager import IncomingQueueManager
# from OutgoingQueueManager import OutgoingQueueManager
# from Packet_buffer import PacketBuffer
# from Timeout import Timeout


class Session:
    """Class for session.
    """
    # třídní proměná pro uchování unikátní id každé instance
    _id: int = 0
    _instances: list['Session'] = []

    def __init__(self,
                 ip,
                 port,
                 reader,
                 writer,
                 session_params: tuple = None,
                 callback_on_message_recv=None,
                 callback_timeouts: tuple = None,
                 send_buffer: Packet_buffer = None,
                 whoami: str = 'client'):

        # Instances of Session
        Session._id += 1
        self.__id: int = Session._id
        Session._instances.append(self)

        # features of session
        self.__reader: asyncio.StreamReader = reader
        self.__writer: asyncio.StreamWriter = writer
        self.__ip_dst: str = ip
        self.__port_dst: int = port
        self.__name: str = "Session_" + str(self.__id)
        # callback
        self.__callback_on_message_recv = callback_on_message_recv

        # events
        # self.__event_queue_in = queue.event_in
        # self.__shared_event_queue_out = queue.event_out
        self.__event_queue_out = asyncio.Event()
        self.__event_update = asyncio.Event()

        # Queues 
        # self.__queue = queue
        # self.__incomming_queue = queue.in_queue
        # self.__outgoing_queue = queue.out_queue
        self.__send_buffer: Packet_buffer = send_buffer
        # self.__recv_buffer = queue.recv_buffer

        # server / client
        self.__whoami: str = whoami

        # local queue is for handle message to update_state_machine
        self.__local_queue = asyncio.Queue(maxsize=256)

        # flag_session = 'START_SESSION'
        # flag_session = 'STOP_SESSION'
        # flag_session = 'ACTIVE_TERMINATION'
        # flag_session = None
        self.__flag_session = None

        # flag_timeout_t1 = 0 - good
        # flag_timeout_t1 = 1 - timeout 
        self.__flag_timeout_t1: int = 0

        # flag for delete self
        self.__flag_stop_tasks: bool = False

        # flag for stop tasks
        self.__flag_delete: bool = False

        # Parameters from config file
        self.__k: int = session_params[0]
        self.__w: int = session_params[1]
        # self.__timeout_t0 = session_params[2]
        self.__timeout_t1: int = session_params[3]
        # self.__timeout_t2 = session_params[4]
        # self.__timeout_t3 = session_params[5]

        # Timers
        # Timer( time, callback)
        self.__timer_t0 = Timer(session_params[2], callback_timeouts[0])
        self.__timer_t1 = Timer(session_params[3], callback_timeouts[1])
        self.__timer_t2 = Timer(session_params[4], callback_timeouts[2])
        self.__timer_t3 = Timer(session_params[5], callback_timeouts[3])
        self.__timers: list[Timer] = [self.__timer_t0,
                                      self.__timer_t1,
                                      self.__timer_t2,
                                      self.__timer_t3]

        # timing of tasks
        self.__async_time: float = 0.5
        self.__time_for_task_timeouts: float = 0.8

        # parameter for select session
        self.__priority: int = 0

        # inical states
        self.__connection_state = ConnectionState.set_state('CONNECTED')
        self.__transmission_state = TransmissionState.set_state('STOPPED')

        # Tasks
        self.__task = None
        self.__tasks: list = []
        # self.__tasks.append(asyncio.create_task(self.handle_messages()))
        # self.__tasks.append(asyncio.create_task(self.send_frame()))

        # if self.__whoami == 'server':
        #     self.__tasks.append(asyncio.create_task(self.update_state_machine_server()))
        # else:
        #     self.__tasks.append(asyncio.create_task(self.update_state_machine_client()))

        # self.__tasks.append(asyncio.create_task(self.check_for_timeouts()))



    async def start(self) -> None:
        self.__task = asyncio.ensure_future(self.handle_messages())
        # await asyncio.gather(*self.__tasks)

    @property
    def k(self) -> int:
        return self.__k

    @property
    def w(self) -> int:
        return self.__w

    @property
    def ip(self) -> str:
        return self.__ip_dst

    @property
    def port(self) -> int:
        return self.__port_dst

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def flag_stop_tasks(self) -> bool:
        return self.__flag_stop_tasks

    @flag_stop_tasks.setter
    def flag_stop_tasks(self, value: bool) -> None:
        self.__flag_stop_tasks = value

    @property
    def event_queue_out(self) -> asyncio.Event:
        return self.__event_queue_out

    @property
    def flag_delete(self) -> bool:
        return self.__flag_delete

    @flag_delete.setter
    def flag_delete(self, flag: bool) -> None:
        print(f"Nastaven flag_delete na {flag}")
        logging.debug(f"Nastaven flag_delete na {flag}")
        self.__flag_delete = flag

    @property
    def flag_session(self) -> int:
        return self.__flag_session

    @flag_session.setter
    def flag_session(self, flag) -> None:
        print(f"flag_session_set {flag} - {self}")
        logging.debug(f"flag_session_set {flag} - {self}")
        self.__flag_session = flag

    @property
    def flag_timeout_t1(self) -> int:
        return self.__flag_timeout_t1

    @flag_timeout_t1.setter
    def flag_timeout_t1(self, flag: int) -> None:
        self.__flag_timeout_t1 = flag

    @property
    def priority(self) -> int:
        return self.__priority

    @property
    def whoami(self) -> str:
        return self.__whoami

    @property
    def connection_state(self) -> str:
        return self.__connection_state.get_state()

    # 0 = DISCONNECTED
    # 1 = CONNECTED
    @connection_state.setter
    def connection_state(self, state) -> None:
        print(f"CHANGE_CONNECTION_STATE: {self.__connection_state} -> {state}")
        logging.debug(f"CHANGE_CONNECTION_STATE: {self.__connection_state} -> {state}")
        self.__connection_state = ConnectionState.set_state(state)

    @property
    def transmission_state(self) -> str:
        return self.__transmission_state.get_state()

    # 0 = STOPPED
    # 1= WAITING_RUNNING
    # 2 = RUNNING
    # 3 = WAITING_UNCONFIRMED
    # 4 = WAITING_STOPPED
    @transmission_state.setter
    def transmission_state(self, state: str) -> None:
        print(f"CHANGE_TRANSMISSION_STATE: {self.__transmission_state} -> {state}")
        logging.debug(f"CHANGE_TRANSMISSION_STATE: {self.__transmission_state} -> {state}")
        self.__transmission_state = TransmissionState.set_state(state)

    @classmethod  # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id_num: int = 0, instance: 'Session' = None) -> bool:
        if instance:
            cls._instances.remove(instance)
            return True
        else:
            return False
        # if id_num < len(cls._instances):
        #     del cls._instances[id_num]
        #     return True
        # else:
        #     return False

    def update_timestamp_t2(self) -> None:
        # self.__timestamp_t2.start()
        self.__timer_t2.start()

    @classmethod
    def get_all_instances(cls) -> list:
        return cls._instances

    @classmethod
    def get_instance(cls, id_num: int) -> Any | None:
        for inst in cls._instances:
            if inst.id == id_num:
                return inst
        return None

    ################################################
    ## RECEIVE FRAME
    async def handle_messages(self) -> None:
        while not self.__flag_stop_tasks:
            # if not self.__flag_stop_tasks:

            # await asyncio.sleep(0.01)  # kritický bod pro rychlost aplikace
            try:
                print(f"Starting async handle_messages")
                logging.debug(f"Starting async handle_messages")

                # zde změřit zda timeout nedělá problém zbrždění
                header = await asyncio.wait_for(self.__reader.read(2), timeout=self.__timeout_t1)
                # header = await self.__reader.read(2)

                if header:
                    start_byte, frame_length = header

                    # identifikace IEC 104
                    if start_byte == Frame.start_byte():

                        apdu = await self.__reader.read(frame_length)
                        if len(apdu) == frame_length:
                            new_apdu = Parser.parser(apdu, frame_length)

                            print(f"{time.strftime('%X')}-Received"
                                  f" from {self.ip}:{self.port}"
                                  f" - frame: {new_apdu}")
                            logging.info(f"{time.strftime('%X')}-Received from"
                                         f" {self.ip}:{self.port}"
                                         f" - frame: {new_apdu}")

                            self.__timer_t0.start()
                            self.__timer_t1.start()
                            self.__timer_t2.start()
                            self.__timer_t3.start()

                            # put into local queue for handle message by update_state
                            # self.__local_queue.put_nowait(new_apdu)

                            # allow to event
                            # self.__event_update.set()

                            # put into incomming queue for handle message by QueueManager
                            # self.__incomming_queue.on_message_received((self, new_apdu))

                            # handle apdu in QueueManager
                            asyncio.ensure_future(self.__callback_on_message_recv(self, new_apdu))

                            # reset local vars
                            header = None
                            start_byte = None
                            apdu = None
                            new_apdu = None
                            frame_length = None
                            # return new_apdu
                            # self.__task = asyncio.ensure_future(self.handle_messages())
                else:
                    print(f"zadne prichozi zpravy")
                    logging.debug(f"zadne prichozi zpravy")

                if self.__reader.at_eof():
                    print(f"EOF - odpojeni klienta")
                    logging.debug(f"EOF - odpojeni klienta")
                    self.flag_session = 'ACTIVE_TERMINATION'
                    asyncio.ensure_future(self.__callback_on_message_recv(self))
                    # allow to event
                    # self.__event_update.set()
                    break

            except asyncio.TimeoutError:
                print(f'Klient {self} neposlal žádná data.')
                logging.debug(f'Klient {self} neposlal žádná data.')
                # if session is still connect, specially in stopped state
                if self.__connection_state != 'DISCONNECTED':
                    # task = asyncio.ensure_future(self.handle_messages())
                    pass

            except Exception as e:
                print(f"Exception v handle_messages {e}")
                logging.error(f"Exception v handle_messages {e}")

            print(f"Finish async handle_messages.")
            logging.debug(f"Finish async handle_messages.")

    ################################################
    ## SEND FRAME
    async def send_frame(self, frame: Frame = None) -> None:
        # while not self.__flag_stop_tasks:
        if not self.__flag_stop_tasks:

            try:
                # # await asyncio.sleep(self.__async_time) # kritický bod pro rychlost ap
                # await self.__event_queue_out.wait()
                # self.__event_queue_out.clear()

                # await self.__shared_event_queue_out.wait()
                # self.__shared_event_queue_out.clear()
                print(f"Start send_frame_task()")
                logging.debug(f"Start send_frame_task()")

                # print("\x1b[31mToto je červený text.\x1b[0m")
                if frame is not None:
                    print(f"{time.strftime('%X')}-Send"
                          f" to {self.ip}:{self.port}"
                          f" - frame: {frame}")
                    logging.info(f"{time.strftime('%X')}-Send"
                                 f" to {self.ip}:{self.port}"
                                 f" - frame: {frame}")
                    self.__writer.write(frame.serialize())
                    await self.__writer.drain()

                # else:
                #     if not self.__outgoing_queue.is_Empty():
                #         print(f"posílá se neco z odchozí fronty")
                #         session, frame = await self.__outgoing_queue.get_message()
                #
                #         if session == self:
                #             print(f"{time.ctime()} - Send frame: {frame}")
                #             self.__writer.write(frame.serialize())
                #             await self.__writer.drain()

                # add to packet buffer
                if isinstance(frame, IFormat):
                    self.__send_buffer.add_frame(frame.ssn, frame)

            except asyncio.QueueEmpty:
                print(f"problem v asynciu - fronta plna")
                logging.error(f"problem v asynciu - fronta plna")
            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

            # reset local var 
            if frame is not None:
                frame = None

            print(f"Stop send_frame_task()")
            logging.debug(f"Stop send_frame_task()")

    @property
    def is_connected(self) -> bool:
        if self.__connection_state == ConnectionState.set_state('CONNECTED'):
            return True
        return False

    @property
    def connection_info(self) -> tuple:
        return self.__ip_dst, self.__port_dst, self.__connection_state, self.__transmission_state

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
                logging.error(f"Zrušení tasku proběhlo úspěšně!")

        for timer_task in self.__timers:
            try:
                timer_task.cancel()
            except asyncio.CancelledError:
                # Zpracování zrušení tasků
                print(f"Zrušení tasku proběhlo úspěšně!")
                logging.error(f"Zrušení tasku proběhlo úspěšně!")

        logging.debug(f"pred smazanim session: {self}")
        Session.remove_instance(instance=self)
        logging.debug(f"po smazani session: {self}")

        del self

    def __enter__(self):
        pass

    def __str__(self) -> str:
        return (f"SessionID: {self.id},"
                f" ip: {self.ip},"
                f" port: {self.port},"
                f" states: {self.connection_state},"
                f" {self.transmission_state}")

    def __exit__(*exc_info):
        pass


