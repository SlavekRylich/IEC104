import asyncio
import time
#from CommModul import CommModule
import struct
from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
import acpi

class QueueManager():
    def __init__(self):
        self.queue = asyncio.Queue()
        # tuple (ip, port, session)
        self.sessions_tuple = []
        self.VR = 0
        self.VS = 0
        self.ack = 0
        self.send_queue = []
        self.sended_queue = []
        self.recv_queue = []
        self.session = None
        
    async def check_for_queue(self):
        if self.queue.empty():
            await asyncio.sleep(0.1)
            return False
        else:
            return True
    
    async def handle_apdu(self, apdu):
        
        print(f"Starting async handle_apdu with {apdu.get_type()}")
        
        if self.session.get_transmission_state() == 'Stopped':
            
            if isinstance(apdu, UFormat):
                if apdu.get_type_int() != acpi.STARTDT_ACT:
                    
                    if apdu.get_type_int() == acpi.TESTFR_ACT:
                        await self.session.response_testdt_con()
                    
                    if apdu.get_type_int() == acpi.TESTFR_CON:
                        pass
                    
                else:
                    await self.session.update_state_machine(apdu)
            else:
                # dle normy -> aktivni ukončení a client si zahájí spojení znovu ??
                pass
            
        if self.session.get_transmission_state() == 'Running':
                    
            if isinstance(apdu, IFormat):
                if (apdu.get_ssn() - self.VR) > 1:
                    # chyba sekvence
                    # vyslat S-format s posledním self.VR
                    raise Exception(f"Invalid SSN: {apdu.get_ssn() - self.VR} > 1")
                    
                else:
                    self.recv_queue.append(apdu)
                    self.incrementVR()
                    self.set_ack(apdu.get_rsn())
                    self.clear_acked_recv_queue()
                
            if isinstance(apdu, SFormat):
                self.set_ack(apdu.get_rsn())
                self.clear_acked_send_queue()
            
            if isinstance(apdu, UFormat):
                if apdu.get_type_int() != acpi.STOPDT_ACT:
                    
                    if apdu.get_type_int() == acpi.TESTFR_ACT:
                        self.session.response_testdt_con()
                    
                    if apdu.get_type_int() == acpi.TESTFR_CON:
                        pass
            
            self.session.update_state_machine(apdu)
            
            #vysílat vygenerovanou odpoved v odesilaci frontě -> implementovat do Session
            if self.isResponse():
                for item in self.get_recv_queue():
                    self.writer.write(item.serialize())
                    await self.writer.drain()
                    
        
        
        if self.session.get_transmission_state() == 'Waiting_unconfirmed':
            
            if isinstance(apdu, SFormat):
                self.set_ack(apdu.get_rsn())
                self.clear_acked_send_queue()
            
            if isinstance(apdu, UFormat):
                
                if apdu.get_type_int() != acpi.STOPDT_ACT:
                    
                    if apdu.get_type_int() == acpi.TESTFR_ACT:
                        self.session.response_testdt_con()
                    
                    if apdu.get_type_int() == acpi.TESTFR_CON:
                        pass
                                
           

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
            
           
            
    # client is tuple (ip, port, session)
    def add_session(self, client):
        ip = client[0] 
        port = client[1]
        session = client[2]
        self.sessions_tuple.append((ip,port,session))
    
    def get_number_of_sessions(self):
        count = 0
        for item in self.sessions_tuple:
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
        for item in self.sessions_tuple:
            if item[2].get_connection_state() == 'Connected' and \
                item[2].get_priority() < 1:
                    self.session = item[2]
                    return self.session
    
    def get_number_of_connected_sessions(self):
        count = 0
        for item in self.sessions_tuple:
            if item[2].get_connection_state() == 'Connected':
                count = count + 1
        return count
    
    def get_connected_sessions(self):
        list = []
        for item in self.sessions_tuple:
            if str(item[2].get_connection_state()) == 'Connected':
                list.append(item[2])   
        return list
    def del_session(self, session):
        for item in self.sessions_tuple:
            if item[2] == session:
                self.sessions_tuple.remove(item)
    
    def get_running_sessions(self):
        for item in self.sessions_tuple:
            if str(item[2].get_transmission_state()) == 'Running':
                return item[2]
    
    def get_sessions_tuple(self):
        return self.sessions_tuple
    
    def get_only_sessions(self):
        list = []
        for item in self.sessions_tuple:
            list.append(item[2])
        return list
    
    def insert_send_queue(self, packet):
        self.send_queue.append(packet)
        
    def insert_recv_queue(self, packet):
        self.recv_queue.append(packet)
    
    def isBlank_send_queue(self):
        for item in self.send_queue():
            return False
        return True
    
    def isBlank_recv_queue(self):
        for item in self.recv_queue():
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
                
    def clear_acked_recv_queue(self):
        for item in self.recv_queue:
            if item.get_ssn() <= self.ack:
                self.recv_queue.remove(item)
                
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
    
    async def check_clients(self):
        
        # .get_sessions_tuple() = tuple (ip, port, session)
        for item in self.get_sessions_tuple():
                        
            print(f"bezi - {item[2]}")
            # timeouts check 
            await item[2].check_for_timeouts()
            
            # client message
            await item[2].check_for_message()
        
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