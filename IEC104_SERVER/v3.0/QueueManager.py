import asyncio

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
    def __init__(self,ip):
        """
        Constructor for QueueManager.

        Args:
            ip (str): IP address.
        """
        self._queue = asyncio.Queue()
        # tuple (ip, port, session)
        self._sessions= []
        self._sessions_new= []
        self._VR = 0
        self._VS = 0
        self._ack = 0
        self._send_queue = []
        self._sended_queue = []
        self._recv_queue = []
        self._session = None
        self._ip = ip
        
        self._in_queue = IncomingQueueManager()
        self._out_queue = OutgoingQueueManager()
        self._packet_buffer = PacketBuffer()
        
        self._async_time = 0.8
        
        self.task_check_in_queue = asyncio.create_task(self.check_in_queue())
        self.task_check_out_queue = asyncio.create_task(self.check_out_queue())
        
        
    async def start(self):
        
        while True:
            print(f"Opakuje se ")
            
            await asyncio.gather(self.task_check_in_queue,
                                 self.task_check_out_queue)
            
            await asyncio.sleep(self._async_time)    
        
    @property
    def in_queue(self):
        return self._in_queue
    
    @property
    def out_queue(self):
        return self._out_queue
    
    @property
    def packet_buffer(self):
        return self._packet_buffer
    
    async def check_in_queue(self):
        while True:
            print(f"Starting_check_in_queue")
            if not self._in_queue.is_Empty():
                    message = await self._in_queue.get_message()
                    await self.handle_apdu(message)
            
            await asyncio.sleep(self._async_time)
            print(f"Finish_check_in_queue")
    
    # is handled in session
    async def check_out_queue(self):    
        while True:
            
            print(f"Starting_check_out_queue")
            if not self._out_queue.is_Empty():
                    pass
                    # message = await self._out_queue.get_message()
                    # self.handle_apdu(message)
                    
            await asyncio.sleep(self._async_time)
            print(f"Finish_check_out_queue")
        
    
    def add_message(self, message):
        self._queue.put_nowait(message)

    async def get_message(self):
        return await self._queue.get()
    
    @property
    def size(self):
        return self._queue.__sizeof__
    
    @property
    def is_Empty(self):
        return self._queue.empty
        
    def add_message(self,message):
        self._queue.put_nowait(message)
        
    @property
    async def message(self):
        return await self._queue.get()
    
    async def on_message_sent(self, message_id):
        pass
    
   
    @property
    def ip(self):
        return self._ip
    
    async def check_for_queue(self):
        if self._queue.empty():
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
        for session in self._sessions:
            if session.connection_state != 'CONNECTED':
                del session
                self._sessions.remove(session)
                
                
        if len(self._sessions) > 0:
            return True
        return False
    
    
    async def handle_apdu(self, apdu):
        
        print(f"Starting async handle_apdu with {apdu}")
        # if isinstance(self._session, Session):
            
        if self._session.transmission_state == 'STOPPED':
            
            if isinstance(apdu, UFormat):
                if apdu._type_int() != acpi.STARTDT_ACT:
                    
                    if apdu._type_int() == acpi.TESTFR_ACT:
                        frame = self.generate_testdt_con()
                        await self._out_queue.to_send(frame)
                        # await self._session.send_frame(frame)
                    
                    if apdu._type_int() == acpi.TESTFR_CON:
                        pass
                    
            
        if self._session.transmission_state == 'RUNNING':
                    
            if isinstance(apdu, IFormat):
                
                if (apdu.ssn() - self._VR) > 1:
                    
                    # chyba sekvence
                    # vyslat S-format s posledním self.VR
                    frame = self.generate_s_frame()
                    await self._out_queue.to_send(frame)
                    # await self._session.send_frame(frame)
                    self._session.flag_session = 'ACTIVE_TERMINATION'
                    # raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")
                    
                else:
                    self.incrementVR()
                    self.ack = apdu.rsn()
                    await self._packet_buffer.clear_group_less_than(self._ack)
                    # await self.clear_acked_recv_queue()
                
                if (self._VR - self._ack) >= self._session.w:
                    frame = self.generate_s_frame()
                    await self._out_queue.to_send(frame)
                    # await self._session.send_frame(frame)
                
            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn()
                await self._packet_buffer.clear_group_less_than(self._ack)
                # await self.clear_acked_send_queue()
            
            if isinstance(apdu, UFormat):
                if apdu._type_int() != acpi.STOPDT_ACT:
                    
                    if apdu._type_int() == acpi.TESTFR_ACT:
                        frame = self.generate_testdt_con()
                        await self._out_queue.to_send(frame)
                        # await self._session.send_frame(frame)
                    
                    if apdu._type_int() == acpi.TESTFR_CON:
                        pass
            
            #vysílat vygenerovanou odpoved v odesilaci frontě -> implementovat do Session
            if self.isResponse():
                for item in self.recv_queue():
                    self.writer.write(item.serialize())
                    await self.writer.drain()
                    
                    # here is important k parameter
                    
        
        
        if self._session.transmission_state == 'WAITING_UNCONFIRMED':
            
            if isinstance(apdu, SFormat):
                self.ack = apdu.rsn()
                await self._packet_buffer.clear_group_less_than(self._ack)
                # self.clear_acked_send_queue()
            
            if isinstance(apdu, UFormat):
                
                if apdu._type_int() != acpi.STOPDT_ACT:
                    
                    if apdu._type_int() == acpi.TESTFR_ACT:
                        frame = self.generate_testdt_con()
                        await self._out_queue.to_send(frame)
                        # await self._session.send_frame(frame)
                    
                    if apdu._type_int() == acpi.TESTFR_CON:
                        pass
                                
        
        
        # await self._session.update_state_machine_server(apdu)                
        print(f"Finish async handle_apdu")

    async def handle_response(self):
        
        
        print(f"Starting async handle_response with ")
        try:
                
            # STATE MACHINE
            if self._session.connection_state == 'CONNECTED':
                
                #* STATE 1
                if self._session.transmission_state == 'STOPPED':
                    
                    # send start act
                    if self._session.flag_session == 'START_SESSION':
                        
                        if self.start_sequence:
                            frame = self.queue.generate_startdt_act()
                            await self._session.send_frame(frame)
                        
                        
                        # resp = await self._session.handle_messages()
                        # if resp:
                        #     if resp.get_type == acpi.STARTDT_ACT:
                                
                    else:
                        # send 2x testdt frame 
                        
                        frame = self.queue.generate_testdt_act()
                        for i in range(0,2):
                            await self._session.send_frame(frame)
                            await asyncio.sleep(0.5)
                        
                
                #* STATE 2
                if self._session.transmission_state == 'WAITING_RUNNING':
                    # else send testdt frame 
                    
                    frame = self.queue.generate_testdt_act()
                    for i in range(0,2):
                        await self._session.send_frame(frame)
                        await asyncio.sleep(0.5)
                
                #* STATE 3
                if self._session.transmission_state == 'RUNNING':
                    
                    # for cyklus for send I frame with random data
                    for frame in self.data_list:
                            # list of data
                            data = self.queue.generate_i_frame(frame)
                            await self._session.send_frame(data)
                            await asyncio.sleep(0.5)
                            
                    # check if response is ack with S format
                    
                    
                    # send testdt frame 
                    frame = self.queue.generate_testdt_act()
                    for i in range(0,2):
                        await self._session.send_frame(frame)
                        await asyncio.sleep(0.5)
                
                #* STATE 4
                if self._session.transmission_state == 'WAITING_UNCONFIRMED':
                    # do not send new I frame, but check if response are I,S or U formats
                    # send testdt frame 
                    frame = self.queue.generate_testdt_act()
                    for i in range(0,2):
                        await self._session.send_frame(frame)
                        await asyncio.sleep(0.5)
                    
                    
                    # check if response is stopdt con
                    frame = self.queue.generate_stopdt_con()
                    await self._session.send_frame(frame)
                
                #* STATE 5
                if self._session.transmission_state == 'WAITING_STOPPED':
                    # # do not send new I frame, but check if response are I,S or U formats
                    # send testdt frame 
                    frame = self.queue.generate_testdt_act()
                    for i in range(0,2):
                        await self._session.send_frame(frame)
                        await asyncio.sleep(0.5)
                            
                    # check if response is stopdt con
                    frame = self.queue.generate_stopdt_con()
                    await self._session.send_frame(frame)
                
                response = await self._session.handle_messages()
                if response:
                    await self._session.update_state_machine_client(response)
            
            self.start_sequence = False
                
                
        except asyncio.CancelledError:
            print(f"CancelledError")
            pass
        except Exception as e:
            print(f"Exception {e}")
    
    def isResponse(self):
        return False        
    
    
    def add_session(self, session):
        self._sessions.append(session)
    
    def get_number_of_sessions(self):
        count = 0
        for item in self._sessions:
            count = count + 1
        return count
    
    def generate_i_frame(self,data):
        new_i_format = IFormat(data, self._VS, self._VR)
        self.incrementVS()
        return new_i_format
    
    def generate_s_frame(self):
        return SFormat(self._VR)
    
    def Select_active_session(self, session):
        # logika výběru aktivního spojení
        # zatím ponechám jedno a to to poslední
        
        # self.sessions = (ip, port, session)
        for session in self._sessions:
            if session.connection_state == 'CONNECTED' and \
                session.priority < 1:
                    self._session = session
                    return self._session
    
    def get_number_of_connected_sessions(self):
        count = 0
        for session in self._sessions:
            if session.connection_state == 'CONNECTED':
                count = count + 1
        return count
    
    def get_connected_sessions(self):
        list = []
        for session in self._sessions:
            if session.connection_state == 'CONNECTED':
                list.append(session)   
        return list
    
    def del_session(self, sess):

        for session in self._sessions:
            if session == sess:
                print(f"Remove by del_session: {session}")
                return self._sessions.remove(session)
        return False
    
    def get_running_sessions(self):
        for session in self._sessions:
            if session.transmission_state == 'RUNNING':
                return session
    @property
    def sessions(self):
        return self._sessions
    
   
    
    def incrementVR(self):
        self._VR = self._VR + 1
    
    def incrementVS(self):
        self._VS = self._VS + 1
        
    @property
    def ack(self):
        return self._ack
    
    @ack.setter
    def ack(self, ack):
        self._ack = ack
    
    @property
    def VR(self):
        return self._VR
    
    @property
    def VS(self):
        return self._VS
    
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
    
    def Uformat_response(self, frame: Frame):
        frame = frame.get_type()
        
        if (frame == acpi.STARTDT_ACT):
            return UFormat(acpi.STARTDT_CON)
        
        elif frame == acpi.STARTDT_CON:
            return None
        
        elif frame == acpi.STOPDT_ACT:
            return UFormat(acpi.STARTDT_CON)
        
        elif frame == acpi.STOPDT_CON:
            return None
        
        elif frame == acpi.TESTFR_ACT:
            return UFormat(acpi.TESTFR_CON)
        
        elif frame == acpi.TESTFR_CON:
            return None
        else:
            return None
    
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