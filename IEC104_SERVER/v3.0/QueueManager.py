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
    def __init__(self,ip, whoami = 'client'):
        """
        Constructor for QueueManager.

        Args:
            ip (str): IP address.
        """
        self.__queue = asyncio.Queue()
        # tuple (ip, port, session)
        self.__sessions= []
        self.__sessions_new= []
        self.__VR = 0
        self.__VS = 0
        self.__ack = 0
        self.__send_queue = []
        self.__sended_queue = []
        self.__recv_queue = []
        self.__session = None
        self.__ip = ip
        
        self.__whoami = whoami
        
        
        self.__start_sequence = True
        
        self.__in_queue = IncomingQueueManager()
        self.__out_queue = OutgoingQueueManager()
        self.__send_buffer = PacketBuffer()
        self.__recv_buffer = PacketBuffer()
        
        self.__async_time = 0.8
        
        self.__task_check_in_queue = asyncio.create_task(self.check_in_queue())
        self.__task_check_out_queue = asyncio.create_task(self.check_out_queue())
        self.__task_check_new_data = asyncio.create_task(self.isResponse())
        
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
        
        
    async def start(self):
        
        while True:
            try:
                await asyncio.gather(self.__task_check_in_queue,
                                 self.__task_check_out_queue,
                                 self.__task_check_new_data)
            except Exception as e:
                print(f"Exception {e}")
                
            await asyncio.sleep(self.__async_time)    
        
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
    
    async def check_in_queue(self):
        while True:
            try:
                print(f"Starting_check_in_queue")
                if not self.__in_queue.is_Empty():
                        message = await self.__in_queue.get_message()
                        if isinstance(message, IFormat):
                            self.__recv_buffer.add_frame(message.ssn,message)
                            
                        if self.__whoami == 'server':
                            await self.handle_apdu(self.__session,message)
                        else:
                            await self.handle_response(self.__session)
                            
            except Exception as e:
                print(f"Exception {e}")            
                        
            await asyncio.sleep(self.__async_time)
            print(f"Finish_check_in_queue")
    
    # is handled in session
    async def check_out_queue(self):    
        while True:
            try:
                print(f"Starting_check_out_queue")
                if not self.__out_queue.is_Empty():
                        pass
                        # message = await self._out_queue.get_message()
                        # self.handle_apdu(message)
                        
                await asyncio.sleep(self.__async_time)
                print(f"Finish_check_out_queue")
                
            except Exception as e:
                print(f"Exception {e}") 
                
    
                    
        
    
    def add_message(self, message):
        self.__queue.put_nowait(message)

    async def get_message(self):
        return await self.__queue.get()
    
    @property
    def size(self):
        return self.__queue.__sizeof__
    
    @property
    def is_Empty(self):
        return self.__queue.empty
        
    def add_message(self,message):
        self.__queue.put_nowait(message)
        
    @property
    async def message(self):
        return await self.__queue.get()
    
    async def on_message_sent(self, message_id):
        pass
    
   
    @property
    def ip(self):
        return self.__ip
    
    async def check_for_queue(self):
        if self.__queue.empty():
            await asyncio.sleep(0.1)
            return False
        else:
            return True
        
    async def check_events_server(self): 
        
        if self.check_alive_sessions():
        
            for session in self.sessions():
                
                await session.check_for_timeouts()
                
                request = await session.handle_messages()
                if request:
                    await self.handle_apdu(request)
                    # ulozit do queue
                    # kontrolovat queue, zda je potřeba neco poslat
                    
                    await session.update_state_machine_server(request)
                    return request
                
                await session.update_state_machine_server()
        
    async def check_events_client(self): 
        
        if self.check_alive_sessions():
        
            for session in self.sessions:
                
                await session.check_for_timeouts()
                try:
                    request = await session.handle_messages()
                    if request:
                        # ulozit do queue
                        # kontrolovat queue, zda je potřeba neco poslat
                        await session.update_state_machine_client(request)
                        return request
                    
                    await session.update_state_machine_client()
                except Exception as e:
                    print(f"Exception {e}")
                    pass
    
    # remove session from sessions list if is not connected
    def check_alive_sessions(self):
        for session in self.__sessions:
            if session.connection_state != 'CONNECTED':
                del session
                self.__sessions.remove(session)
                
                
        if len(self.__sessions) > 0:
            return True
        return False
    
    
    async def handle_apdu(self,session, apdu):
        
        print(f"Starting async handle_apdu with {apdu}")
        # if isinstance(self._session, Session):
        
        actual_transmission_state = session.transmission_state
            
        if actual_transmission_state == 'STOPPED':
            
            if isinstance(apdu, UFormat):
                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    await self.__out_queue.to_send(frame)
                
                    
        if actual_transmission_state == 'RUNNING':
                    
            if isinstance(apdu, IFormat):
                
                if (apdu.ssn - self.__VR) > 1:
                    
                    # chyba sekvence
                    # vyslat S-format s posledním self.VR
                    frame = await self.generate_s_frame(session)
                    await self.__out_queue.to_send(frame)
                    # await self._session.send_frame(frame)
                    session.flag_session = 'ACTIVE_TERMINATION'
                    # raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")
                    
                else:
                    self.incrementVR()
                    self.ack = apdu.rsn
                    self.__send_buffer.clear_frames_less_than(self.__ack)
                    
                    # # odpověď stejnymi daty jen pro testovani 
                    # new_apdu = self.generate_i_frame(apdu.data)
                    # await self.__out_queue.to_send(new_apdu)
                
                if self.__recv_buffer.__len__() >= session.w:
                    frame = await self.generate_s_frame(session)
                    await self.__out_queue.to_send(frame)
                
            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                self.__send_buffer.clear_frames_less_than(self.__ack)
            
            if isinstance(apdu, UFormat):
                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    await self.__out_queue.to_send(frame)
                
        
        if actual_transmission_state == 'WAITING_UNCONFIRMED':
            
            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn
                self.__send_buffer.clear_frames_less_than(self.__ack)
                # self.clear_acked_send_queue()
            
            if isinstance(apdu, UFormat):
                
                if apdu.type_int == acpi.TESTFR_ACT:
                    frame = self.generate_testdt_con()
                    await self.__out_queue.to_send(frame)
                                
                    
        print(f"Finish async handle_apdu")

    async def handle_response(self, session):
        
        print(f"Starting async handle_response ")
        actual_transmission_state = session.transmission_state
        try:
                
            # STATE MACHINE
            if session.connection_state == 'CONNECTED':
                
                #* STATE 1
                if actual_transmission_state == 'STOPPED':
                    
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        await self.__out_queue.to_send(frame)
                        await asyncio.sleep(2.5)
                        
                    # send start act
                    if self.__start_sequence:
                        session.flag_session = 'START_SESSION'
                    
                
                #* STATE 2
                if actual_transmission_state == 'WAITING_RUNNING':
                    # else send testdt frame 
                    
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        await self.__out_queue.to_send(frame)
                        await asyncio.sleep(2.5)
                
                #* STATE 3
                if actual_transmission_state == 'RUNNING':
                    
                    # for cyklus for send I frame with random data
                    for data in self.data_list:
                            # list of data
                            frame = self.generate_i_frame(data, session)
                            await self.__out_queue.to_send(frame)
                            await asyncio.sleep(1.5)
                            
                    # check if response is ack with S format
                    
                    if self.__recv_buffer.__len__() >= session.w:
                        frame = await self.generate_s_frame(session)
                        await self.__out_queue.to_send(frame)
                    
                    # send testdt frame 
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        await self.__out_queue.to_send(frame)
                        await asyncio.sleep(2.5)
                        
                    await asyncio.sleep(10)
                    session.flag_session = 'STOP_SESSION'
                
                #* STATE 4
                if actual_transmission_state == 'WAITING_UNCONFIRMED':
                    # do not send new I frame, but check if response are I,S or U formats
                    # send testdt frame 
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        await self.__out_queue.to_send(frame)
                        await asyncio.sleep(2.5)
                    
                    # session.flag_session = 'STOP_SESSION'
                
                #* STATE 5
                if actual_transmission_state == 'WAITING_STOPPED':
                    # # do not send new I frame, but check if response are I,S or U formats
                    # send testdt frame 
                    frame = self.generate_testdt_act()
                    for i in range(0,2):
                        await self.__out_queue.to_send(frame)
                        await asyncio.sleep(2.5)
                            
                    # check if response is stopdt con
                    # frame = self.generate_stopdt_con()
                    # await self.__out_queue.to_send(frame)
                
            self.__start_sequence = False
                
                
        except asyncio.CancelledError:
            print(f"CancelledError")
            pass
        except Exception as e:
            print(f"Exception {e}")
    
    async def isResponse(self):
        await asyncio.sleep(self.__async_time)
        return False        
    
    
    def add_session(self, session):
        self.__sessions.append(session)
        self.__session = self.Select_active_session(session)
    
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
                return self.__sessions.remove(session)
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
    
    async def check_events(self):
        
        # .get_sessions_tuple() = tuple (ip, port, session)
        for session in self.sessions:
                        
            print(f"bezi - {session}")
            # timeouts check 
            await session.check_for_timeouts()
            
            # client message
            await session.check_for_message()

        # queue check
        await self.check_for_queue()
        
    def __enter__():
        pass    
    
    def __exit__(*exc_info):
        pass