import time
#from CommModul import CommModule
import struct
from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
import acpi

class QueueManager():
    def __init__(self, socket=None):
        self.socket = socket
        self.VR = 0
        self.VS = 0
        self.ACK = 0
        self.queue = []
        
    def insert(self, packet):
        self.queue.append(packet)
    
    def clear_acked(self):
        for item in self.queue:
            if item.get_ssn() <= self.ACK:
                self.queue.remove(item)
        
    def incrementVR(self):
        self.VR = self.VR + 1
    
    def incrementVS(self):
        self.VS = self.VS + 1
        
    def setACK(self, ack):
        self.ACK = ack
        
    def getVR(self):
        return self.VR
    
    def getVS(self):
        return self.VS
    
    def getACK(self):
        return self.ACK
    
    def Uformat(self, frame):
        frame = frame.get_type()
        
        if (frame == acpi.STARTDT_ACT):
            return UFormat(acpi.STARTDT_CON)
            return acpi.STARTDT_CON
        elif frame == acpi.STARTDT_CON:
            return None
        elif frame == acpi.STOPDT_ACT:
            return UFormat(acpi.STARTDT_CON)
        elif frame == acpi.STARTDT_CON:
            return None
        elif frame == acpi.TESTFR_ACT:
            return UFormat(acpi.TESTFR_CON)
        elif frame == acpi.TESTFR_CON:
            return None
        else:
            return None
    
    
    def enqueue_request(self, request_data, callback): # Přidá nový požadavek do fronty s odpovídajícím callbackem na zpracování odpovědi.
        pass
    
    def dequeue_request(self): # Vrací a odstraňuje nejstarší požadavek z fronty.
        pass
    
    def process_response(self,response_data): # Zpracuje příchozí odpověď a vyvolá odpovídající callback.
        pass
    
    def pair_requests(self, request1, request2): # Propojí dva požadavky, např. pro výzvu a odpověď.
        pass
    
    def remove_request(request_id): # Odebere požadavek z fronty na základě jeho identifikátoru.
        pass

    def get_pending_requests(): # Vrátí seznam všech nevyřízených požadavků.
        pass

    def get_waiting_responses(): # Vrátí seznam všech čekajících odpovědí.
        pass

    def handle_timeout(request_id): # Zpracuje timeout pro konkrétní požadavek.
        pass

    def handle_error(request_id, error): # Zpracuje chybu pro konkrétní požadavek.
        pass

    def get_connection_status(): # Vrátí informace o aktuálním stavu spojení.
        pass

    def reconnect(): # Opětovné připojení k serveru v případě přerušení spojení.
        pass

# class QueueManager():
#     def __init__(self):
#         self.request_queue = QueueManager()
#         self.response_queue = QueueManager()
#         self.request_callbacks = {}

    def enqueue_request(self, request_data, callback):
        request_id = self.generate_request_id()
        self.request_queue.put((request_id, request_data))
        self.request_callbacks[request_id] = callback
        return request_id

    def generate_request_id(self):
        # Tato metoda by mohla generovat unikátní identifikátory pro požadavky
        return str(time.time())

    def process_responses(self):
        while not self.response_queue.empty():
            response_id, response_data = self.response_queue.get()
            if response_id in self.request_callbacks:
                callback = self.request_callbacks.pop(response_id)
                callback(response_data)

    def simulate_server_response(self):
        while True:
            if not self.request_queue.empty():
                request_id, request_data = self.request_queue.get()
                # Simulace zpracování požadavku na straně serveru
                response_data = f"Odpověď na {request_data}"
                self.response_queue.put((request_id, response_data))
            time.sleep(2)
    
    def __enter__():
        pass    
    
    def __exit__(*exc_info):
        pass