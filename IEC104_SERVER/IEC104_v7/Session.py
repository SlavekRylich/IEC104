# -*- coding: utf-8 -*-

import logging
from datetime import datetime

import asyncio
from typing import Any

import Packet_buffer
from Timer import Timer
from Frame import Frame
from Parser import Parser
from IFormat import IFormat
from State import ConnectionState, TransmissionState


class Session:
    """
    Class for session. Manages communication with a client and handles incoming and outgoing frames.
    """

    def __init__(self,
                 id: int,
                 ip: str,
                 port: int,
                 reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter,
                 session_params: tuple = None,
                 callback_on_message_recv=None,
                 callback_timeouts: tuple = None,
                 callback_for_delete=None,
                 send_buffer: Packet_buffer = None,
                 whoami: str = 'client'):
        """
        Initialize a new Session instance.

        :param ip: IP address of the client.
        :param port: Port number of the client.
        :param reader: asyncio.StreamReader for reading data from the client.
        :param writer: asyncio.StreamWriter for writing data to the client.
        :param session_params: Tuple of parameters for the session.
        :param callback_on_message_recv: Callback function to handle received messages.
        :param callback_timeouts: Tuple of callback functions for handling timeouts.
        :param send_buffer: Packet_buffer for storing outgoing frames.
        :param whoami: String indicating whether the session is for a client or server.
        """

        self.__id: int = id

        # features of session
        self.__reader: asyncio.StreamReader = reader
        self.__writer: asyncio.StreamWriter = writer
        self.__ip_dst: str = ip
        self.__port_dst: int = port
        self.__name: str = "Session_" + str(self.__id)
        # callback
        self.__callback_on_message_recv: Any = callback_on_message_recv
        self.__callback_for_delete: Any = callback_for_delete
        # events
        # self.__event_queue_in = queue.event_in
        # self.__shared_event_queue_out = queue.event_out
        self.__event_queue_out: asyncio.Event = asyncio.Event()
        self.__event_update: asyncio.Event = asyncio.Event()

        # Sending buffer from ClientManager
        self.__send_buffer: Packet_buffer = send_buffer

        # server_app / client_app
        self.__whoami: str = whoami

        # local queue is for handle message to update_state_machine
        # self.__local_queue: asyncio.Queue = asyncio.Queue(maxsize=256)

        # flag_session = 'START_SESSION'
        # flag_session = 'STOP_SESSION'
        # flag_session = 'ACTIVE_TERMINATION'
        # flag_session = None
        self.__flag_session: str | None = None

        # flag_timeout_t1 = 0 - good
        # flag_timeout_t1 = 1 - timeout 
        self.__flag_timeout_t1: bool = False

        # flag for delete self
        self.__flag_stop_tasks: bool = False

        # flag for stop tasks
        self.__flag_delete: bool = False

        # Parameters from config file
        self.__k: int = session_params[0]
        self.__w: int = session_params[1]
        self.__timeout_t1: int = session_params[3]

        # Timers
        # Timer( time, callback)
        self.__timer_t0 = Timer(session_params[2], callback_timeouts[0])
        self.__timer_t1 = Timer(session_params[3], callback_timeouts[1])
        self.__timer_t2 = Timer(session_params[4], callback_timeouts[2])
        self.__timer_t3 = Timer(session_params[5], callback_timeouts[3])
        self.__timers: list[Timer] = [self.__timer_t0,
                                      self.__timer_t1,
                                      self.__timer_t2,
                                      self.__timer_t3
                                      ]

        # timing of tasks

        # init states
        self.__connection_state: ConnectionState = ConnectionState.set_state('CONNECTED')
        self.__transmission_state: TransmissionState = TransmissionState.set_state('STOPPED')

        # Tasks
        self.__task_handle_messages: asyncio.Task | None = None
        self.__tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """
        Start the session by initiating the handling of incoming messages.
        """
        self.__task_handle_messages = asyncio.ensure_future(self.handle_messages())
        self.__tasks.append(self.__task_handle_messages)

    @property
    def k(self) -> int:
        """
        Return the value of k.
        """
        return self.__k

    @property
    def w(self) -> int:
        """
        Return the value of w.
        """
        return self.__w

    @property
    def ip(self) -> str:
        """
        Return the IP address.
        """
        return self.__ip_dst

    @property
    def port(self) -> int:
        """
        Return the port.
        """
        return self.__port_dst

    @property
    def id(self) -> int:
        """
        Return the value of id.
        """
        return self.__id

    @property
    def name(self) -> str:
        """
        Return the name of the session.
        """
        return self.__name

    @property
    def flag_stop_tasks(self) -> bool:
        """
        Return the flag indicating whether to stop the tasks for the session.
        """
        return self.__flag_stop_tasks

    @flag_stop_tasks.setter
    def flag_stop_tasks(self, value: bool) -> None:
        """
        Set the flag indicating whether to stop the tasks for the session.

        :param value: The new value for the flag.
        """
        self.__flag_stop_tasks = value

    @property
    def event_queue_out(self) -> asyncio.Event:
        return self.__event_queue_out

    @property
    def flag_delete(self) -> bool:
        """
        Return the flag indicating whether to delete the session.

        Returns
        -------
        bool
            The flag indicating whether to delete the session.
        """
        return self.__flag_delete

    @flag_delete.setter
    def flag_delete(self, flag: bool) -> None:
        """
        Set the flag indicating whether to delete the session.

        Parameters
        ----------
        flag : bool
            The new value for the flag.
        """
        print(f"flag_delete set to {flag}")
        logging.debug(f"flag_delete set to {flag}")
        self.__flag_delete = flag

    @property
    def flag_session(self) -> str | None:
        """
        Return the flag indicating the session state.

        Returns
        -------
        str | None
            The flag indicating the session state.
        """
        return self.__flag_session

    @flag_session.setter
    def flag_session(self, flag: str) -> None:
        """
        Set the flag indicating the session state.

        Parameters
        ----------
        flag : str
            The new value for the flag.
        """
        print(f"flag_session set to {flag} - {self}")
        logging.debug(f"flag_session set to {flag} - {self}")
        self.__flag_session = flag

    @property
    def flag_timeout_t1(self) -> bool:
        """
        Return the flag indicating whether a timeout occurred for timer T1.

        Returns
        -------
        bool
            The flag indicating whether a timeout occurred for timer T1.
        """
        return self.__flag_timeout_t1

    @flag_timeout_t1.setter
    def flag_timeout_t1(self, flag: bool) -> None:
        """
        Set the flag indicating whether a timeout occurred for timer T1.

        Parameters
        ----------
        flag : bool
            The new value for the flag.
        """
        print(f"flag_timeout_t1 set to - {flag}")
        logging.debug(f"Timer t1 timed_out - {flag}")
        self.__flag_timeout_t1 = flag

    @property
    def whoami(self) -> str:
        """
        Return the identifier for the session (client or server).

        Returns
        -------
        str
            The identifier for the session.
        """
        return self.__whoami

    @property
    def connection_state(self) -> str:
        """
        Return the connection state of the session.

        Returns
        -------
        str
            The connection state of the session.
        """
        return self.__connection_state.get_state()

    # 0 = DISCONNECTED
    # 1 = CONNECTED
    @connection_state.setter
    def connection_state(self, state) -> None:
        """
        Set the connection state of the session.

        Parameters
        ----------
        state : str
            The new connection state of the session.
        """
        print(f"CHANGE_CONNECTION_STATE: {self.__connection_state} -> {state}")
        logging.debug(f"CHANGE_CONNECTION_STATE: {self.__connection_state} -> {state}")
        self.__connection_state = ConnectionState.set_state(state)

    @property
    def transmission_state(self) -> str:
        """
        Return the transmission state of the session.

        Returns
        -------
        str
            The transmission state of the session.
        """
        return self.__transmission_state.get_state()

    # 0 = STOPPED
    # 1= WAITING_RUNNING
    # 2 = RUNNING
    # 3 = WAITING_UNCONFIRMED
    # 4 = WAITING_STOPPED
    @transmission_state.setter
    def transmission_state(self, state: str) -> None:
        """
        Set the transmission state of the session.

        Parameters
        ----------
        state : str
            The new transmission state of the session.
        """
        print(f"CHANGE_TRANSMISSION_STATE: {self.__transmission_state} -> {state}")
        logging.debug(f"CHANGE_TRANSMISSION_STATE: {self.__transmission_state} -> {state}")
        self.__transmission_state = TransmissionState.set_state(state)

    def update_timestamp_t2(self) -> None:
        # self.__timestamp_t2.start()
        self.__timer_t2.start()

    # RECEIVE FRAME
    async def handle_messages(self) -> None:
        """
        Asynchronously handle incoming messages from the client.
        """
        while not self.__flag_stop_tasks:

            try:
                print(f"Starting async handle_messages()")
                logging.debug(f"Starting async handle_messages()")

                # read
                header = await asyncio.wait_for(self.__reader.read(2), timeout=self.__timeout_t1)
                if header:
                    start_byte, frame_length = header
                    # identify IEC 104
                    if start_byte == Frame.start_byte():
                        # read the rest of frame
                        apdu = await self.__reader.read(frame_length)
                        if len(apdu) == frame_length:
                            new_apdu = Parser.parser(apdu, frame_length)

                            # print(f"{datetime.now().strftime("%H:%M:%S:%f")}-Received"
                            #       f" from {self.ip}:{self.port}"
                            #       f" - frame: {new_apdu}")
                            # logging.debug(f"{datetime.now().strftime("%H:%M:%S:%f")}-Received from"
                            #               f" {self.ip}:{self.port}"
                            #               f" - frame: {new_apdu}")
                            # update timers
                            self.__timer_t0.start()
                            self.__timer_t1.start()
                            self.__timer_t2.start()
                            self.__timer_t3.start()

                            # handle apdu in QueueManager
                            task = asyncio.ensure_future(self.__callback_on_message_recv(self, new_apdu))
                            self.__tasks.append(task)

                            # reset local vars
                            header = None
                            start_byte = None
                            apdu = None
                            new_apdu = None
                            frame_length = None
                else:
                    print(f"Nothing frame from client.")
                    logging.debug(f"Nothing frame from client.")

                if self.__reader.at_eof():
                    print(f"Receive EOF")
                    logging.debug(f"Receive EOF")
                    self.flag_session = 'ACTIVE_TERMINATION'
                    task = asyncio.ensure_future(self.__callback_on_message_recv(self))
                    self.__tasks.append(task)
                    break

            except asyncio.TimeoutError:
                print(f'Client {self} hasn\'t send any frames.')
                logging.debug(f'Client {self} hasn\'t send any frames.')
                # # if session is still connect, specially in stopped state
                # self.flag_session = 'ACTIVE_TERMINATION'
                # task = asyncio.ensure_future(self.__callback_on_message_recv(self))
                # self.__tasks.append(task)

            except Exception as e:
                print(f"Exception in handle_messages {e}")
                logging.error(f"Exception in handle_messages {e}")
                self.flag_session = 'ACTIVE_TERMINATION'
                task = asyncio.ensure_future(self.__callback_on_message_recv(self))
                self.__tasks.append(task)
                break

            print(f"Finish async handle_messages.")
            logging.debug(f"Finish async handle_messages.")

    ################################################
    # SEND FRAME
    async def send_frame(self, frame: Frame = None) -> None:
        """
        Asynchronously send a frame to the client.

        :param frame: The frame to be sent.
        """

        if not self.__flag_stop_tasks:
            try:
                print(f"Start send_frame_task()")
                logging.debug(f"Start send_frame_task()")

                if frame is not None:
                    # add to packet buffer
                    if isinstance(frame, IFormat):
                        self.__send_buffer.add_frame(frame.ssn, frame)

                    # print(f"{datetime.now().strftime("%H:%M:%S:%f")}-Send"
                    #       f" to {self.ip}:{self.port}"
                    #       f" - frame: {frame}")
                    # logging.debug(f"{datetime.now().strftime("%H:%M:%S:%f")}-Send"
                    #               f" to {self.ip}:{self.port}"
                    #               f" - frame: {frame}")

                    self.__writer.write(frame.serialize())
                    await self.__writer.drain()

            except Exception as e:
                print(f"Exception {e}")
                logging.error(f"Exception {e}")

            print(f"Stop send_frame_task()")
            logging.debug(f"Stop send_frame_task()")

    def delete_self(self) -> None:
        """
        Delete the session and perform necessary cleanup.
        """

        # flag for stop coroutines
        self.flag_stop_tasks = True
        # flag for delete instance by ClientManager
        self.flag_delete = True

        for task in self.__tasks:
            try:
                task.cancel()

            except asyncio.CancelledError:
                # Zpracování zrušení tasků
                print(f"Task in session be canceled successfully!")
                logging.debug(f"Task in session be canceled successfully!")

        for timer_task in self.__timers:
            try:
                timer_task.cancel()

            except asyncio.CancelledError:
                # Zpracování zrušení tasků
                print(f"Task in session be canceled successfully!")
                logging.debug(f"Task in session be canceled successfully!")

        self.__callback_for_delete(self)
        del self

    def __str__(self) -> str:
        """
        Return a string representation of the Session instance.
        """
        return (f"SessionID: {self.id},"
                f" ip: {self.ip},"
                f" port: {self.port},"
                f" states: {self.connection_state},"
                f" {self.transmission_state}")

    def __exit__(*exc_info):
        pass
