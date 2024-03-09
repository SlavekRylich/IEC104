from ast import List
import asyncio

import acpi
from Session import Session
from Frame import Frame

from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat

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
        self._sessions: List[Session]= []
        self._VR = 0
        self._VS = 0
        self._ack = 0
        self._send_queue = []
        self._sended_queue = []
        self._recv_queue = []
        self._session = None
        self._ip = ip
        
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
                
                request = await session.handle_messages()
                if request:
                    # ulozit do queue
                    # kontrolovat queue, zda je potřeba neco poslat
                    await session.update_state_machine_client(request)
                    return request
                
                await session.update_state_machine_client()
    
    
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
        if isinstance(self._session, Session):
            
            if self._session.transmission_state == 'STOPPED':
                
                if isinstance(apdu, UFormat):
                    if apdu.get_type_int() != acpi.STARTDT_ACT:
                        
                        if apdu.get_type_int() == acpi.TESTFR_ACT:
                            frame = self._session.generate_testdt_con()
                            await self._session.send_frame(frame)
                        
                        if apdu.get_type_int() == acpi.TESTFR_CON:
                            pass
                        
                
            if self._session.transmission_state == 'RUNNING':
                        
                if isinstance(apdu, IFormat):
                    
                    if (apdu.get_ssn() - self._VR) > 1:
                        
                        # chyba sekvence
                        # vyslat S-format s posledním self.VR
                        frame = self.generate_s_frame()
                        await self._session.send_frame(frame)
                        self._session.flag_session = 'ACTIVE_TERMINATION'
                        # raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")
                        
                    else:
                        self._recv_queue.append(apdu)
                        self.incrementVR()
                        self.ack(apdu.get_rsn())
                        await self.clear_acked_recv_queue()
                    
                    if (self._VR - self._ack) >= self._session.w:
                        frame = self.generate_s_frame()
                        await self._session.send_frame(frame)
                    
                if isinstance(apdu, SFormat):
                    self.ack(apdu.get_rsn())
                    await self.clear_acked_send_queue()
                
                if isinstance(apdu, UFormat):
                    if apdu.get_type_int() != acpi.STOPDT_ACT:
                        
                        if apdu.get_type_int() == acpi.TESTFR_ACT:
                            frame = self._session.generate_testdt_con()
                            await self._session.send_frame(frame)
                        
                        if apdu.get_type_int() == acpi.TESTFR_CON:
                            pass
                
                #vysílat vygenerovanou odpoved v odesilaci frontě -> implementovat do Session
                if self.isResponse():
                    for item in self.recv_queue():
                        self.writer.write(item.serialize())
                        await self.writer.drain()
                        
                        # here is important k parameter
                        
            
            
            if self._session.transmission_state == 'WAITING_UNCONFIRMED':
                
                if isinstance(apdu, SFormat):
                    self.ack(apdu.get_rsn())
                    self.clear_acked_send_queue()
                
                if isinstance(apdu, UFormat):
                    
                    if apdu.get_type_int() != acpi.STOPDT_ACT:
                        
                        if apdu.get_type_int() == acpi.TESTFR_ACT:
                            frame = self._session.generate_testdt_con()
                            await self._session.send_frame(frame)
                        
                        if apdu.get_type_int() == acpi.TESTFR_CON:
                            pass
                                    
            
            
            await self._session.update_state_machine_server(apdu)                
            print(f"Finish async handle_apdu")

    async def handle_send_queue(self):
        """
        Vyprázdní frontu odesílání dat odesláním všech položek.
        """
        for frame in self._send_queue:
            
            # move to sended queue
            self._sended_queue.append(frame)
            # remove frame from send queue
            self._send_queue.remove(frame)
            # send frame
            frame = await self._session.send_frame(frame)
            
           
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
        
    def insert_send_queue(self, packet):
        self._send_queue.append(packet)
        
    def insert_recv_queue(self, packet):
        self._recv_queue.append(packet)
    
    def isBlank_send_queue(self):
        for item in self._send_queue:
            return False
        return True
    
    def isBlank_recv_queue(self):
        for item in self._recv_queue:
            return False
        return True
    
    @property
    def send_queue(self):
        return self._send_queue
    
    @property
    def recv_queue(self):
        return self._recv_queue
    
    
    def clear_acked_send_queue(self):
        for item in self._send_queue:
            if item.get_ssn() <= self._ack:
                self._send_queue.remove(item)
                
    async def clear_acked_recv_queue(self):
        for item in self._recv_queue:
            if item.get_ssn() <= self._ack:
                self._recv_queue.remove(item)
            
    def get_len_recv_queue(self):
        return len(self._recv_queue)
    
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
    
    def Uformat_response(self, frame: Frame):
        frame = frame.get_type()
        
        if (frame == acpi.STARTDT_ACT):
            return UFormat(acpi.STARTDT_CON)
            return acpi.STARTDT_CON
        
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
        for session in self.sessions():
                        
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