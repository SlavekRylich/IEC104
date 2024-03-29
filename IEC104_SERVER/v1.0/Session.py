import socket
import logging
import asyncio
import Frame
import acpi
from Parser import Parser
from State import StateConn,StateTrans
from Timeout import Timeout
from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat

LISTENER_LIMIT=5
# Konfigurace logování
logging.basicConfig(
    filename='server_log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# # Příklad logování
# logging.info('Server starting...')
# logging.debug('Debugging information')
# logging.warning('Warning message')
# logging.error('Error occurred')
# logging.critical('Critical error')

# # Pro uzavření logovacího souboru
# logging.shutdown()

class Session():
    # třídní proměná pro uchování unikátní id každé instance
    id = 0
    instances = []
    
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.timeout = 0
        self.sessions = []
        self.server_clients = []
        
        self.connection_state = StateConn.set_state('Connected')
        self.transmission_state = StateTrans.set_state('Stopped')
        
        
        Session.id += 1
        self.id = Session.id
        Session.instances.append(self)
    
    # 0 = Disconnected
    # 1 = Connected
    def set_connection_state(self, state):
        self.connection_state = state
    
    # 0 = Stopped
    # 1= Pending_running
    # 2 = Running
    # 3 = Pending_unconfirmed
    # 4 = Pending_stopped
    def set_transmission_state(self, state):
        self.connection_state = state
    
    def get_connection_state(self):
        return self.connection_state.get_state()
    
    def get_transmission_state(self):
        return self.connection_state.get_state()
        
    @classmethod        # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id = 0, instance = None):
        if not id:  # zde rezerva*
            if instance: 
                cls.instances.remove(instance)
                return True
            else:
                return False
        
        if id < len(cls.instances):
            del cls.instances[id]
            return True
        else:
            return False
    
    @classmethod
    def get_all_instances(cls):
        return cls.instances
    
    @classmethod
    def get_instance(cls, id):
        for inst in cls.instances:
            if inst.id == id:
                return inst
        return None
            
    def accept(self):
        while True:
            self.client, self.address = self.socket.accept()
            self.sessions.append(self.client)
            return (self.client, self.address)
        
    async def accept_async(self):
        while True:
            
            self.client = await self.socket.accept()
            self.sessions.append(self.client)
            return self.client
        
    def receive_data(self):
        buffer = 0
        while True:
            data = self.socket.recv(1)
            
            if not data:
                break
            buffer += data
        return buffer
    
    async def receive_data_async(self):
        buffer = 0
        while True:
            data = await self.socket.recv(1)
            
            if not data:
                break
            buffer += data
        return buffer
        
    async def handle_messages(self, reader, writer):
        self.reader = reader
        self.writer = writer
        while True:
            try:
                # Příjem zpráv a zpracování
                print(f"\n\n\nSu připraven přijímat data...")

                header = await self.reader.read(2)
                
                if not header:
                    return 0
                
                start_byte, frame_length = header
                
                # identifikace IEC 104
                if start_byte == Frame.Frame.start_byte:
                    apdu = await self.reader.read(frame_length)
                    if len(apdu) == frame_length:
                        new_apdu = Parser.parser(apdu,frame_length)
                        
                        return new_apdu
                
                # přijat nějaký neznámý formát
                      
            except Exception as e:
                print(f"Exception {e}")

    async def send_message(self, message):
        # Odeslat zprávu na hlavní nebo záložní spojení
        pass
    
    async def keepalive(self):
        test_frame = UFormat(acpi.TESTFR_ACT)
        self.writer(test_frame.serialize())
        await self.writer.drain()
        
    async def response_testdt_act(self):
        test_frame = UFormat(acpi.TESTFR_ACT)
        self.writer(test_frame.serialize())
        await self.writer.drain()
    
    async def response_testdt_con(self):
        test_frame = UFormat(acpi.TESTFR_CON)
        self.writer(test_frame.serialize())
        await self.writer.drain()
    
    async def response_startdt_act(self):
        test_frame = UFormat(acpi.STARTDT_ACT)
        self.writer(test_frame.serialize())
        await self.writer.drain()
    
    async def response_startdt_con(self):
        test_frame = UFormat(acpi.STARTDT_CON)
        self.writer(test_frame.serialize())
        await self.writer.drain()
        
    async def response_stopdt_act(self):
        test_frame = UFormat(acpi.STOPDT_ACT)
        self.writer(test_frame.serialize())
        await self.writer.drain()
        
    async def response_stopdt_con(self):
        test_frame = UFormat(acpi.STOPDT_CON)
        self.writer(test_frame.serialize())
        await self.writer.drain()
        
    async def send_frame(self,frame):
        self.writer(frame.serialize())
        await self.writer.drain()
        
    
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip,self.port))
        logging.info(f"Connected to {self.ip}:{self.port}")
        self.connected = True
        return self.socket


    def start_server(self):
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip,self.port))
        self.socket.listen(LISTENER_LIMIT)
        logging.info(f"Server listening on {self.ip}:{self.port}")
        return self.socket

    def disconnect(self):
        logging.info(f"Disconnecting")
        self.connected = False
        self.sessions.remove(self.client)
        self.socket.close()
                
        
        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket.bind((self.ip,self.port))
        # self.socket.listen(LISTENER_LIMIT)
        # logging.info(f"Server listening on {self.ip}:{self.port}")

    async def connect_async(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        await self.socket.connect((self.ip,self.port))
        logging.info(f"Connected to {self.ip}:{self.port}")
        return self.socket
        
    def send_data(self, data):
        return self.socket.send(data)
        
    async def send_data_async(self, data):
        return await self.socket.send(data)
    
    def is_connected(self):
        return self.connected
    
    def handle_error(self, error):
        pass
    
    def set_timeout(self, timeout):
        self.timeout = timeout
        
    def get_connection_info(self):
        return self.ip, self.port, self.connected, self.timeout
    
    def reconnect(self):
        pass
        
    def __enter__():
        pass
        
    def __exit__(*exc_info):
        pass