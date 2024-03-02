import socket
import logging
import asyncio
import time
import Frame
import acpi
from Parser import Parser
from State import StateConn,StateTrans
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
    
    def __init__(self, ip, port, reader, writer, queue=0, session_params=0):
        self.reader = reader
        self.writer = writer
        self.ip = ip
        self.port = port
        self.timestamp = time.ctime()
        self.sessions = []
        self.queue = queue
        
        self.k = session_params.k
        self.w = session_params.w
        self.timeout_t0 = session_params.timeout_t0
        self.timeout_t1 = session_params.timeout_t1
        self.timeout_t2 = session_params.timeout_t2
        self.timeout_t3 = session_params.timeout_t3
        
        # param for select session
        self.priority = 0
        
        self.connection_state = StateConn.set_state('Connected')
        self.transmission_state = StateTrans.set_state('Stopped')
        
        
        Session.id += 1
        self.id = Session.id
        Session.instances.append(self)
    
    def get_priority(self):
        return self.priority
    
    def add_queue(self, queue):
        self.queue = queue
    
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
    def update_timestamp(self):
        self.timestamp = time.ctime()
        
    def get_timestamp(self):
        return self.timestamp
    
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
        
    async def handle_messages(self):
        
        self.loop = asyncio.get_running_loop()
        try:
            while True:
                # Příjem zpráv a zpracování
                print(f"\n\n\nSu připraven přijímat data...")

                header = await asyncio.wait_for(self.reader.read(2),timeout=2)
                
                if not header:
                    await asyncio.sleep(1)
                    continue
                
                start_byte, frame_length = header
                
                # identifikace IEC 104
                if start_byte == Frame.Frame.start_byte:
                    apdu = await self.reader.read(frame_length)
                    if len(apdu) == frame_length:
                        new_apdu = Parser.parser(apdu,frame_length)
                        self.update_timestamp()
                        
                        if isinstance(new_apdu, UFormat):
                            self.loop.create_task(self.handle_U_format(new_apdu))
                            
                            
                            # return new_apdu
                        await self.queue.add_frame(new_apdu)
                        # return new_apdu
                    
            # přijat nějaký neznámý formát
        except asyncio.TimeoutError:
            print(f'Client {self.ip} timed out due to inactivity')
        except asyncio.CancelledError:
            pass         
        except Exception as e:
            print(f"Exception {e}")
    
    async def handle_U_format(self, apdu):
        apdu = apdu.get_type()
        
        if (apdu == acpi.STARTDT_ACT):
            await self.response_startdt_con()
            
            
        elif apdu == acpi.STOPDT_ACT:
            await self.response_stopdt_con()
            
        elif apdu == acpi.TESTFR_ACT:
            await self.response_testdt_con()
            
    async def send_message(self, message):
        # Odeslat zprávu na hlavní nebo záložní spojení
        pass
    
    async def keepalive(self):
        frame = UFormat(acpi.TESTFR_ACT)
        self.writer(frame.serialize())
        await self.writer.drain()
        
    async def response_testdt_act(self):
        frame = UFormat(acpi.TESTFR_ACT)
        self.writer(frame.serialize())
        await self.writer.drain()
    
    async def response_testdt_con(self):
        frame = UFormat(acpi.TESTFR_CON)
        self.writer(frame.serialize())
        await self.writer.drain()
    
    async def response_startdt_act(self):
        frame = UFormat(acpi.STARTDT_ACT)
        self.writer(frame.serialize())
        await self.writer.drain()
    
    async def response_startdt_con(self):
        frame = UFormat(acpi.STARTDT_CON)
        self.writer(frame.serialize())
        await self.writer.drain()
        
    async def response_stopdt_act(self):
        frame = UFormat(acpi.STOPDT_ACT)
        self.writer(frame.serialize())
        await self.writer.drain()
        
    async def response_stopdt_con(self):
        frame = UFormat(acpi.STOPDT_CON)
        self.writer(frame.serialize())
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
    
    async def check_for_timeouts(self):
        # Projděte si slovník klientů a zkontrolujte jejich timeout
        time_now = time.time()
        last_timestamp = self.get_timestamp()
        
        if time_now - last_timestamp > self.timeout_t0:
            print(f'Client {self.ip}:{self.port} timed out and disconnected')
            # self.loop.create_task()
            
        if time_now - last_timestamp > self.timeout_t1:
            
            self.set_transmission_state('Stopped')
            self.set_connection_state('Disconnected')
            raise Exception(f"Timeout pro t1")
            # connection close
            # self.loop.create_task()
            
        if time_now - last_timestamp > self.timeout_t2:
            resp = self.queue.response_S_format()
            await self.send_frame(resp)
            # self.loop.create_task()
            
        if time_now - last_timestamp > self.timeout_t3:
            await self.response_testdt_act()
            # self.loop.create_task()
    
    
    def update_state_machine(self, fr = 0):
        
            # set_connection_state()
                # 0 = Disconnected
                # 1 = Connected
            if  self.get_connection_state('Connected'):
                
            # get_connection_state()
                # 0 = Stopped
                # 1= Pending_running
                # 2 = Running
                # 3 = Pending_unconfirmed
                # 4 = Pending_stopped
                
                # spravny format pro podminky 
                if isinstance(fr, UFormat):
                    frame = fr.get_type_int()
                
                else:
                    frame = fr.get_type_in_word()   # S-format
                
                # STATE 1   - if stopped and U-frame(STARTDT ACT)
                if self.get_transmission_state() == 'Stopped' and \
                    frame == acpi.STARTDT_ACT:
                    
                    # poslat STARTDT CON
                    self.set_transmission_state('Running')
                    self.response_startdt_con()
                    
                # #   - if stopped and U-frame(other)
                # if  self.active_session.get_transmission_state() and \
                #     frame != acpi.STARTDT_ACT:
                        
                #     self.active_session.set_transmission_state(2)
                
                # STATE 2   - if running and U-frame(STOPDT ACT) and send_queue is blank
                if self.get_transmission_state() == 'Running' and \
                    frame == acpi.STOPDT_ACT and \
                        not self.queue.isBlank_send_queue():
                            
                            # poslat STOPDT CON
                        self.set_transmission_state('Stopped')
                        self.response_stopdt_con()
                        
                        
                # STATE 2   - if running and U-frame(STOPDT ACT) and send_queue is not blank
                if self.get_transmission_state() == 'Running' and \
                    frame == acpi.STOPDT_ACT and \
                        self.queue.isBlank_send_queue():
                            
                            # poslat STOPDT CON
                        self.set_transmission_state('Pending_unconfirmed')
                
                
                # STATE 3   - if Pending_unconfirmed and S-Frame and send_queue is blank
                if self.get_transmission_state() == 'Pending_unconfirmed' and \
                    frame.get_type_in_word() == 'S-format' and \
                        not self.queue.isBlank_send_queue():
                            
                            # poslat STOPDT CON
                        self.set_transmission_state('Stopped')
                        self.response_stopdt_con()
                    
            else:
                self.set_transmission_state('Stopped')
                self.set_connection_state('Disconnected')
                pass
    
    
    def reconnect(self):
        pass
        
    def __enter__():
        pass
        
    def __exit__(*exc_info):
        pass