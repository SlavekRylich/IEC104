import asyncio
import time
from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
import acpi

class QueueManager():
    def __init__(self,ip, port):
        self.queue = asyncio.Queue()
        # tuple (ip, port, session)
        self.sessions = []
        self.VR = 0
        self.VS = 0
        self.ack = 0
        self.send_queue = []
        self.sended_queue = []
        self.recv_queue = []
        self.session = None
        self.ip = ip
        
    def get_ip(self):
        return self.ip
    
    async def check_for_queue(self):
        if self.queue.empty():
            await asyncio.sleep(0.1)
            return False
        else:
            return True
    async def check_events_server(self): 
        
        if self.check_alive_sessions():
        
            for session in self.get_sessions():
                
                await session.check_for_timeouts()
                
                request = await session.handle_messages()
                if request:
                    # ulozit do queue
                    # kontrolovat queue, zda je potřeba neco poslat
                    
                    await session.update_state_machine_server(request)
                    return request
                
                await session.update_state_machine_server()
        
    async def check_events_client(self): 
        
        
        self.check_alive_sessions()
        
        for session in self.get_sessions():
            
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
        for session in self.sessions:
            if session.get_connection_state() != 'CONNECTED':
                del session
                self.sessions.remove(session)
                
                
        if len(self.sessions) > 0:
            return True
        return False
    
    
    async def handle_apdu(self, apdu):
        
        print(f"Starting async handle_apdu with {apdu}")
        
        if self.session.get_transmission_state() == 'STOPPED':
            
            if isinstance(apdu, UFormat):
                if apdu.get_type_int() != acpi.STARTDT_ACT:
                    
                    if apdu.get_type_int() == acpi.TESTFR_ACT:
                        frame = self.session.generate_testdt_con()
                        await self.session.send_frame(frame)
                    
                    if apdu.get_type_int() == acpi.TESTFR_CON:
                        pass
                    
            
        if self.session.get_transmission_state() == 'RUNNING':
                    
            if isinstance(apdu, IFormat):
                
                if (apdu.get_ssn() - self.VR) > 1:
                    
                    # chyba sekvence
                    # vyslat S-format s posledním self.VR
                    frame = self.generate_s_frame()
                    await self.session.send_frame(frame)
                    self.session.set_flag_session('ACTIVE_TERMINATION')
                    # raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")
                    
                else:
                    self.recv_queue.append(apdu)
                    self.incrementVR()
                    self.set_ack(apdu.get_rsn())
                    self.clear_acked_recv_queue()
                
                if (self.VR - self.ack) >= self.session.get_w():
                    frame = self.generate_s_frame()
                    await self.session.send_frame(frame)
                
            if isinstance(apdu, SFormat):
                self.set_ack(apdu.get_rsn())
                self.clear_acked_send_queue()
            
            if isinstance(apdu, UFormat):
                if apdu.get_type_int() != acpi.STOPDT_ACT:
                    
                    if apdu.get_type_int() == acpi.TESTFR_ACT:
                        frame = self.session.generate_testdt_con()
                        await self.session.send_frame(frame)
                    
                    if apdu.get_type_int() == acpi.TESTFR_CON:
                        pass
            
            #vysílat vygenerovanou odpoved v odesilaci frontě -> implementovat do Session
            if self.isResponse():
                for item in self.get_recv_queue():
                    self.writer.write(item.serialize())
                    await self.writer.drain()
                    
                    # here is important k parameter
                    
        
        
        if self.session.get_transmission_state() == 'WAITING_UNCONFIRMED':
            
            if isinstance(apdu, SFormat):
                self.set_ack(apdu.get_rsn())
                self.clear_acked_send_queue()
            
            if isinstance(apdu, UFormat):
                
                if apdu.get_type_int() != acpi.STOPDT_ACT:
                    
                    if apdu.get_type_int() == acpi.TESTFR_ACT:
                        frame = self.session.generate_testdt_con()
                        await self.session.send_frame(frame)
                    
                    if apdu.get_type_int() == acpi.TESTFR_CON:
                        pass
                                
           
        
        await self.session.update_state_machine_server(apdu)                
        print(f"Finish async handle_apdu")

    async def handle_send_queue(self):
        """
        Vyprázdní frontu odesílání dat odesláním všech položek.
        """
        for frame in self.send_queue:
            
            # move to sended queue
            self.sended_queue.append(frame)
            # remove frame from send queue
            self.send_queue.remove(frame)
            # send frame
            frame = await self.session.send_frame(frame)
            
           
    def isResponse(self):
        return False        
    
    
    def add_session(self, session):
        self.sessions.append(session)
    
    def get_number_of_sessions(self):
        count = 0
        for item in self.sessions:
            count = count + 1
        return count
    
    def generate_i_frame(self,data):
        return IFormat(data, self.VS, self.VR)
    
    def generate_s_frame(self):
        return SFormat(self.VR)
    
    def Select_active_session(self, session):
        # logika výběru aktivního spojení
        # zatím ponechám jedno a to to poslední
        
        # self.sessions = (ip, port, session)
        for session in self.sessions:
            if session.get_connection_state() == 'CONNECTED' and \
                session.get_priority() < 1:
                    self.session = session
                    return self.session
    
    def get_number_of_connected_sessions(self):
        count = 0
        for session in self.sessions:
            if session.get_connection_state() == 'CONNECTED':
                count = count + 1
        return count
    
    def get_connected_sessions(self):
        list = []
        for session in self.sessions:
            if session.get_connection_state() == 'CONNECTED':
                list.append(session)   
        return list
    
    def del_session(self, sess):
        for session in self.sessions:
            if session == sess:
                print(f"Remove by del_session: {session}")
                self.sessions.remove(session)
    
    def get_running_sessions(self):
        for session in self.sessions:
            if session.get_transmission_state() == 'RUNNING':
                return session
    
    def get_sessions(self):
        return self.sessions
        
    def insert_send_queue(self, packet):
        self.send_queue.append(packet)
        
    def insert_recv_queue(self, packet):
        self.recv_queue.append(packet)
    
    def isBlank_send_queue(self):
        for item in self.send_queue:
            return False
        return True
    
    def isBlank_recv_queue(self):
        for item in self.recv_queue:
            return False
        return True
    
    def get_send_queue(self):
        return self.send_queue
    
    def get_recv_queue(self):
        return self.recv_queue
    
    
    def clear_acked_send_queue(self):
        for item in self.send_queue:
            if item.get_ssn() <= self.ack:
                self.send_queue.remove(item)
                
    async def clear_acked_recv_queue(self):
        for item in self.recv_queue:
            if item.get_ssn() <= self.ack:
                self.recv_queue.remove(item)
            
    def get_len_recv_queue(self):
        return len(self.recv_queue)
    
    def incrementVR(self):
        self.VR = self.VR + 1
    
    def incrementVS(self):
        self.VS = self.VS + 1
        
    def set_ack(self, ack):
        self.ack = ack
        
    def get_VR(self):
        return self.VR
    
    def get_VS(self):
        return self.VS
    
    def get_ack(self):
        return self.ack
    
    def Uformat_response(self, frame):
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
        for session in self.get_sessions():
                        
            print(f"bezi - {session}")
            # timeouts check 
            await session.check_for_timeouts()
            
            # client message
            await session.check_for_message()

            
            
        # queue check
        await self.check_for_queue()

# class QueueManager():
#     def __init__(self):
#         self.request_queue = QueueManager()
#         self.response_queue = QueueManager()
#         self.request_callbacks = {}

    # def enqueue_request(self, request_data, callback):
    #     request_id = self.generate_request_id()
    #     self.request_queue.put((request_id, request_data))
    #     self.request_callbacks[request_id] = callback
    #     return request_id

    # def generate_request_id(self):
    #     # Tato metoda by mohla generovat unikátní identifikátory pro požadavky
    #     return str(time.time())

    # def process_responses(self):
    #     while not self.response_queue.empty():
    #         response_id, response_data = self.response_queue.get()
    #         if response_id in self.request_callbacks:
    #             callback = self.request_callbacks.pop(response_id)
    #             callback(response_data)

    # def simulate_server_response(self):
    #     while True:
    #         if not self.request_queue.empty():
    #             request_id, request_data = self.request_queue.get()
    #             # Simulace zpracování požadavku na straně serveru
    #             response_data = f"Odpověď na {request_data}"
    #             self.response_queue.put((request_id, response_data))
    #         time.sleep(2)
    
    def __enter__():
        pass    
    
    def __exit__(*exc_info):
        pass