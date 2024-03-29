import asyncio
import struct

import acpi
from Frame import Frame

from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
from IncomingQueueManager import IncomingQueueManager
from OutgoingQueueManager import OutgoingQueueManager
from Packet_buffer import PacketBuffer

class QueueManager():
    """
    Class for queue manager.
    """
    __id = 0
    __instances = []
    
    def __init__(self,ip, whoami = 'client'):
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
        self.__in_queue = IncomingQueueManager(self.__event_queue_in)
        self.__out_queue = OutgoingQueueManager(self.__shared_event_queue_out)
        
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
        
        self.data_list = [self.data2, self.data2]     # define static data
        
        QueueManager.__id += 1
        self.__id = QueueManager.__id
        QueueManager.__instances.append(self)
        print(f"NOVA INSTANCE QUEUE ID: {self.__id}")
        
    async def start(self):
        try:
            self.__tasks.append(asyncio.create_task(self.check_in_queue()))
            # self.__tasks.append(asyncio.create_task(self.check_out_queue()))
            self.__tasks.append(asyncio.create_task(self.isResponse()))
            self.__tasks.append(asyncio.create_task(self.check_alive_sessions()))
        
        
        
            await asyncio.gather(*self.__tasks)
        except Exception as e:
            print(f"Exception {e}")
            
            # await asyncio.sleep(self.__async_time)    
    @property
    def flag_delete(self):
        return self.__flag_delete
    
    @property
    def event_in(self,):
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
                
                if not self.__in_queue.is_Empty():
                    
                        session, message = await self.__in_queue.get_message()
                        
                        if isinstance(message, IFormat):
                            self.__recv_buffer.add_frame(message.ssn, message)
                            
                        if self.__whoami == 'server':
                            await self.handle_apdu(session, message)
                        else:
                            await self.handle_apdu(session, message)
                            await self.handle_response(session)
                            
                        await asyncio.sleep(self.__async_time)
                        print(f"Finish_check_in_queue")    
                        
            except Exception as e:
                print(f"Exception {e}")            
                        
            
            session = None
            message = None
    
    # is handled in session
    async def check_out_queue(self):    
        while not self.__flag_stop_tasks:
            
            try:
                print(f"Starting_check_out_queue")
                if not self.__out_queue.is_Empty():
                    pass
                print(f"Finish_check_out_queue")
                await asyncio.sleep(self.__async_time)
            except Exception as e:
                print(f"Exception {e}") 
                
            
                    
        
   
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
                        self.__flag_stop_tasks = True
                        break
                    else:
                        await asyncio.sleep(self.__async_time)
                        print(f"tady nastalo continue")
                        continue
                else: 
                    # some session is connected        
                    self.__flag_no_sessions = True
                    
                    print(f"tady je pripojeny 1 a vic klientu")
                    # check if flag for delete session
                    for sess in self.__sessions:
                        if sess.flag_delete:
                            
                            print(f"v session je nastaven priznak na delete")
                            self.__sessions.remove(sess)
                            del sess
                
                await asyncio.sleep(self.__async_time)

            except Exception as e:
                print(f"Exception {e}")
            
            
        self.delete_self()
        
    def delete_self(self):
        for task in self.__tasks:
            try:
                task.cancel()
                        
            except asyncio.CancelledError:
                # Zpracování zrušení tasků
                print(f"Zrušení tasku proběhlo úspěšně!")
            
        self.__flag_delete = True
    
    # for client and server
    async def handle_apdu(self,session, apdu):
        
        print(f"Starting async handle_apdu with {apdu}")
        # if isinstance(self._session, Session):
        
        actual_transmission_state = session.transmission_state
        session_event = session.event_queue_out
            
        if actual_transmission_state == 'STOPPED' or\
            actual_transmission_state == 'WAITING_RUNNING':
            
            if isinstance(apdu, UFormat):
                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    self.__out_queue.to_send((session,frame), session_event)
        
                    
        if actual_transmission_state == 'RUNNING':
                    
            if isinstance(apdu, IFormat):
                
                if (apdu.ssn - self.__VR) > 1:
                    
                    # chyba sekvence
                    # vyslat S-format s posledním self.VR
                    frame = await self.generate_s_frame(session)
                    self.__out_queue.to_send((session,frame), session_event)
                    # await self._session.send_frame(frame)
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
                    self.__out_queue.to_send((session,frame), session_event)
                
            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                await self.__send_buffer.clear_frames_less_than(self.__ack)
            
            if isinstance(apdu, UFormat):
                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    self.__out_queue.to_send((session,frame), session_event)
                
        
        if actual_transmission_state == 'WAITING_UNCONFIRMED' and\
            session.whoami == 'server':
            
            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                await self.__send_buffer.clear_frames_less_than(self.__ack)
                # self.clear_acked_send_queue()
            
            if isinstance(apdu, UFormat):
                
                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    self.__out_queue.to_send((session,frame), session_event)
                    
        if session.whoami == 'client' and\
            (actual_transmission_state == 'WAITING_UNCONFIRMED' or\
            actual_transmission_state == 'WAITING_STOPPED'):
                
            if isinstance(apdu, IFormat): 
                   
                if (apdu.ssn - self.__VR) > 1:
                        # chyba sekvence
                        # vyslat S-format s posledním self.VR
                        frame = await self.generate_s_frame(session)
                        self.__out_queue.to_send((session,frame), session_event)
                        session.flag_session = 'ACTIVE_TERMINATION'
                        # raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")
                        
                else:
                    self.incrementVR()
                    self.ack = apdu.rsn
                    await self.__send_buffer.clear_frames_less_than(self.__ack)
                
                if self.__recv_buffer.__len__() >= session.w:
                    frame = await self.generate_s_frame(session)
                    self.__out_queue.to_send((session,frame), session_event)
                    
            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                await self.__send_buffer.clear_frames_less_than(self.__ack)
            
            if isinstance(apdu, UFormat):
                
                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    self.__out_queue.to_send((session,frame), session_event)
                                
                  
        print(f"Finish async handle_apdu")

    async def handle_response(self, session):
        
        print(f"Starting async handle_response ")
        actual_transmission_state = session.transmission_state
        session_event = session.event_queue_out
        
        try:
                
            # STATE MACHINE
            if session.connection_state == 'CONNECTED':
                
                #* STATE 1
                if actual_transmission_state == 'STOPPED':
                    
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        self.__out_queue.to_send((session,frame), session_event)
                        await asyncio.sleep(2.5)
                        
                    # send start act
                    if self.__flag_start_sequence:
                        session.flag_session = 'START_SESSION'
                    
                
                #* STATE 2
                if actual_transmission_state == 'WAITING_RUNNING':
                    # else send testdt frame 
                    
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        self.__out_queue.to_send((session,frame), session_event)
                        await asyncio.sleep(2.5)
                
                #* STATE 3
                if actual_transmission_state == 'RUNNING':
                    
                    # for cyklus for send I frame with random data
                    for data in self.data_list:
                            # list of data
                            frame = self.generate_i_frame(data, session)
                            self.__out_queue.to_send((session,frame), session_event)
                            await asyncio.sleep(1.5)
                            
                    # check if response is ack with S format
                    
                    if self.__recv_buffer.__len__() >= session.w:
                        frame = await self.generate_s_frame(session)
                        self.__out_queue.to_send((session,frame), session_event)
                    
                    # send testdt frame 
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        self.__out_queue.to_send((session,frame), session_event)
                        await asyncio.sleep(2.5)
                        
                    await asyncio.sleep(10)
                    session.flag_session = 'STOP_SESSION' 
                    print(f"nastaven priznak 'STOP_SESSION'")
                
                #* STATE 4
                if actual_transmission_state == 'WAITING_UNCONFIRMED':
                    # do not send new I frame, but check if response are I,S or U formats
                    # send testdt frame 
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        self.__out_queue.to_send((session,frame), session_event)
                        await asyncio.sleep(2.5)
                    
                    # session.flag_session = 'STOP_SESSION'
                
                #* STATE 5
                if actual_transmission_state == 'WAITING_STOPPED':
                    # # do not send new I frame, but check if response are I,S or U formats
                    # send testdt frame 
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        self.__out_queue.to_send((session,frame), session_event)
                        await asyncio.sleep(2.5)
                            
                    # check if response is stopdt con
                    # frame = self.generate_stopdt_con()
                    # self.__out_queue.to_send((session,frame), session_event)
                
            self.__flag_start_sequence = False
                
                
        except Exception as e:
            print(f"Exception {e}")
    
    async def isResponse(self):
        while not self.__flag_stop_tasks:
            try:
                await asyncio.sleep(self.__async_time)
            except Exception as e:
                print(f"Exception {e}")
               
    
    
    def add_session(self, session):
        self.__sessions.append(session)
        # self.__session = self.Select_active_session(session)
    
    def get_number_of_sessions(self):
        count = 0
        for item in self.__sessions:
            count = count + 1
        return count
    
    def generate_i_frame(self,data, session):
        session.update_timestamp_t2()
        new_i_format = IFormat(data, self.__VS, self.__VR)
        self.incrementVS()
        return new_i_format
    
    async def generate_s_frame(self, session):
        session.update_timestamp_t2()
        await self.__recv_buffer.clear_frames_less_than(self.__VR)
        return SFormat(self.__VR)
    
    def Select_active_session(self, session):
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
        list = []
        for session in self.__sessions:
            if session.connection_state == 'CONNECTED':
                list.append(session)   
        return list
    
    def del_session(self, sess):

        for session in self.__sessions:
            if session == sess:
                print(f"Remove by del_session: {session}")
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
    
    def __str__(self):
        return f"Fronta: {self.ip}, ID: {self.id} připojeno: {len(self.sessions)} sessions"  
    
    def __enter__():
        pass    
    
    def __exit__(*exc_info):
        pass