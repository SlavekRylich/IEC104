import logging
import asyncio
import time

import acpi
from Timer import Timer
from Frame import Frame
from Parser import Parser
from IFormat import IFormat
from State import StateConn, StateTrans

# from IncomingQueueManager import IncomingQueueManager
# from OutgoingQueueManager import OutgoingQueueManager
# from Packet_buffer import PacketBuffer
# from Timeout import Timeout


class Session:
    """Class for session.
    """
    # třídní proměná pro uchování unikátní id každé instance
    _id = 0
    _instances = []

    def __init__(self,
                 ip,
                 port,
                 reader,
                 writer,
                 session_params=None,
                 callback_handle_apdu=None,
                 callback_timeouts=None,
                 send_buffer=None,
                 whoami='client'):

        # features of session
        self.__reader = reader
        self.__writer = writer
        self.__ip_dst = ip
        self.__port_dst = port

        # callback
        self.__callback_handle_apdu = callback_handle_apdu

        # events
        # self.__event_queue_in = queue.event_in
        # self.__shared_event_queue_out = queue.event_out
        self.__event_queue_out = asyncio.Event()
        self.__event_update = asyncio.Event()

        # Queues 
        # self.__queue = queue
        # self.__incomming_queue = queue.in_queue
        # self.__outgoing_queue = queue.out_queue
        self.__send_buffer = send_buffer
        # self.__recv_buffer = queue.recv_buffer

        # server / client
        self.__whoami = whoami

        # local queue is for handle message to update_state_machine
        self.__local_queue = asyncio.Queue(maxsize=256)

        # flag_session = 'START_SESSION'
        # flag_session = 'STOP_SESSION'
        # flag_session = 'ACTIVE_TERMINATION'
        # flag_session = None
        self.__flag_session = None

        # flag_timeout_t1 = 0 - good
        # flag_timeout_t1 = 1 - timeout 
        self.__flag_timeout_t1 = 0

        # flag for delete self
        self.__flag_stop_tasks = False

        # flag for stop tasks
        self.__flag_delete = False

        # Parameters from config file
        self.__k = session_params[0]
        self.__w = session_params[1]
        # self.__timeout_t0 = session_params[2]
        self.__timeout_t1 = session_params[3]
        # self.__timeout_t2 = session_params[4]
        # self.__timeout_t3 = session_params[5]

        # Timers
        # Timer( time, callback)
        self.__timer_t0 = Timer(session_params[2], callback_timeouts[0])
        self.__timer_t1 = Timer(session_params[3], callback_timeouts[1])
        self.__timer_t2 = Timer(session_params[4], callback_timeouts[2])
        self.__timer_t3 = Timer(session_params[5], callback_timeouts[3])

        # timing of tasks
        self.__async_time = 0.5
        self.__time_for_task_timeouts = 0.8

        # parameter for select session
        self.__priority = 0

        # inical states
        self.__connection_state = StateConn.set_state('CONNECTED')
        self.__transmission_state = StateTrans.set_state('STOPPED')

        # Tasks
        self.__task = None
        self.__tasks = []
        # self.__tasks.append(asyncio.create_task(self.handle_messages()))
        # self.__tasks.append(asyncio.create_task(self.send_frame()))

        # if self.__whoami == 'server':
        #     self.__tasks.append(asyncio.create_task(self.update_state_machine_server()))
        # else:
        #     self.__tasks.append(asyncio.create_task(self.update_state_machine_client()))

        # self.__tasks.append(asyncio.create_task(self.check_for_timeouts()))

        Session._id += 1
        self.__id = Session._id
        Session._instances.append(self)

    async def start(self):
        self.__task = asyncio.ensure_future(self.handle_messages())
        # await asyncio.gather(*self.__tasks)

    @property
    def k(self):
        return self.__k

    @property
    def w(self):
        return self.__w

    @property
    def ip(self):
        return self.__ip_dst

    @property
    def port(self):
        return self.__port_dst

    @property
    def id(self):
        return self.__id

    @property
    def flag_stop_tasks(self):
        return self.__flag_stop_tasks

    @property
    def event_queue_out(self):
        return self.__event_queue_out

    @property
    def flag_delete(self):
        return self.__flag_delete

    @flag_delete.setter
    def flag_delete(self, flag):
        print(f"Nastaven flag_delete na {flag}")
        logging.debug(f"Nastaven flag_delete na {flag}")
        self.__flag_delete = flag

    @property
    def flag_session(self):
        return self.__flag_session

    @flag_session.setter
    def flag_session(self, flag):
        print(f"flag_session_set {flag}")
        logging.debug(f"flag_session_set {flag}")
        self.__flag_session = flag

    @property
    def flag_timeout_t1(self):
        return self.__flag_timeout_t1

    @flag_timeout_t1.setter
    def flag_timeout_t1(self, flag):
        self.__flag_timeout_t1 = flag

    @property
    def priority(self):
        return self.__priority

    @property
    def whoami(self):
        return self.__whoami

    @property
    def connection_state(self):
        return self.__connection_state.get_state()

    # 0 = DISCONNECTED
    # 1 = CONNECTED
    @connection_state.setter
    def connection_state(self, state):
        print(f"CHANGE_CONNECTION_STATE: {self.__connection_state} -> {state}")
        logging.debug(f"CHANGE_CONNECTION_STATE: {self.__connection_state} -> {state}")
        self.__connection_state = StateConn.set_state(state)

    @property
    def transmission_state(self):
        return self.__transmission_state.get_state()

    # 0 = STOPPED
    # 1= WAITING_RUNNING
    # 2 = RUNNING
    # 3 = WAITING_UNCONFIRMED
    # 4 = WAITING_STOPPED
    @transmission_state.setter
    def transmission_state(self, state):
        print(f"CHANGE_TRANSMISSION_STATE: {self.__transmission_state} -> {state}")
        logging.debug(f"CHANGE_TRANSMISSION_STATE: {self.__transmission_state} -> {state}")
        self.__transmission_state = StateTrans.set_state(state)

    @classmethod  # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id=0, instance=None):
        if not id:  # zde rezerva*
            if instance:
                cls._instances.remove(instance)
                return True
            else:
                return False

        if id < len(cls._instances):
            del cls._instances[id]
            return True
        else:
            return False

    def update_timestamp_t2(self):
        # self.__timestamp_t2.start()
        self.__timer_t2.start()

    @classmethod
    def get_all_instances(cls):
        return cls._instances

    @classmethod
    def get_instance(cls, id: int):
        for inst in cls._instances:
            if inst.id == id:
                return inst
        return None

    ################################################
    ## RECEIVE FRAME
    async def handle_messages(self):
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
                            callback_task = asyncio.ensure_future(self.__callback_handle_apdu(self, new_apdu))

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
    async def send_frame(self, frame: Frame = None):
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
    def is_connected(self):
        if self.__connection_state == StateConn.set_state('CONNECTED'):
            return True
        return False

    @property
    def connection_info(self):
        return self.__ip_dst, self.__port_dst, self.__connection_state, self.__transmission_state, self._timeout

    def delete_self(self):
        for task in self.__tasks:
            try:
                task.cancel()

            except asyncio.CancelledError:
                # Zpracování zrušení tasků
                print(f"Zrušení tasku proběhlo úspěšně!")
                logging.error(f"Zrušení tasku proběhlo úspěšně!")

        self.__flag_delete = True

    def __enter__(self):
        pass

    def __str__(self):
        return (f"SessionID: {self.id},"
                f" ip: {self.ip},"
                f" port: {self.port},"
                f" states: {self.connection_state},"
                f" {self.transmission_state}")

    def __exit__(*exc_info):
        pass

