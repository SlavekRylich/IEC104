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
    
    def __init__(self, ip, port, reader, writer, session_params=0):
        self.reader = reader
        self.writer = writer
        self.ip = ip
        self.port = port
        self.timestamp = time.time()
        self.queue = None
        
        # flag_session = 'START_SESSION'
        # flag_session = 'STOP_SESSION'
        # flag_session = 'ACTIVE_TERMINATION'
        # flag_session = None
        self.flag_session = None 
        
        # flag_timeout_t1 = 0 - good
        # flag_timeout_t1 = 1 - timeout 
        self.flag_timeout_t1 = 0
        
        self.k = session_params[0]
        self.w = session_params[1]
        self.timeout_t0 = session_params[2]
        self.timeout_t1 = session_params[3]
        self.timeout_t2 = session_params[4]
        self.timeout_t3 = session_params[5]
        
        # param for select session
        self.priority = 0
        
        # inical states
        self.connection_state = StateConn.set_state('CONNECTED')
        self.transmission_state = StateTrans.set_state('STOPPED')
        
        
        Session.id += 1
        self.id = Session.id
        Session.instances.append(self)
    
    def get_k(self):
        return self.k
    
    def get_w(self):
        return self.w
    
    def get_ip(self):
        return self.ip
    
    def get_port(self):
        return self.port
    def get_id(self):
        return self.id
    
    def set_flag_session(self, flag):
        self.flag_session = flag
        
    def get_flag_session(self):
        return self.flag_session
    
    def set_flag_timeout_t1(self, flag):
        self.flag_timeout_t1 = flag
        
    def get_flag_timeout_t1(self):
        return self.flag_timeout_t1
    
    def get_priority(self):
        return self.priority
    
    def add_queue(self, queue):
            self.queue = queue
    
    # 0 = DISCONNECTED
    # 1 = CONNECTED
    def set_connection_state(self, state):
        self.connection_state = StateConn.set_state(state)
    
    # 0 = STOPPED
    # 1= WAITING_RUNNING
    # 2 = RUNNING
    # 3 = WAITING_UNCONFIRMED
    # 4 = WAITING_STOPPED
    def set_transmission_state(self, state):
        self.transmission_state = StateTrans.set_state(state)
    
    def get_connection_state(self):
        return self.connection_state.get_state()
    
    def get_transmission_state(self):
        return self.transmission_state.get_state()
        
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
        self.timestamp = time.time()
        
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
        
    
        
    async def check_for_message(self):
        if self.connection_state == StateConn.set_state('CONNECTED'):
                await self.handle_messages()
            
    async def handle_messages(self):
        
        self.loop = asyncio.get_running_loop()
        try:
            print(f"Starting async handle_messages")
            
            header = await asyncio.wait_for(self.reader.read(2),timeout=0.5)
            
            if header:
                start_byte, frame_length = header
                
                # identifikace IEC 104
                if start_byte == Frame.Frame.start_byte:
                    apdu = await self.reader.read(frame_length)
                    if len(apdu) == frame_length:
                        new_apdu = Parser.parser(apdu,frame_length)
                        
                        # aktualizace poslední aktivity 
                        self.update_timestamp()
                        
                        # if isinstance(new_apdu, UFormat):
                        #     self.loop.create_task(self.handle_U_format(new_apdu))
                        
                        print(f"{time.ctime()} - Přijat rámec: {new_apdu}")
                        print(f"Finish async handle_messages.")
                        
                        return new_apdu
            else:
                print(f"doslo k tomuto vubec nekdy?")
                return None
                        
                    
            # přijat nějaký neznámý formát
        except asyncio.TimeoutError:
            print(f'Klient {self} neposlal žádná data.')
            
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
            
    
    
    ##############################################
    ## RESPONSES
    async def keepalive(self):
        frame = UFormat(acpi.TESTFR_ACT)
        self.writer.write(frame.serialize())
        await self.writer.drain()
        
    ################################################
    ## SEND FRAME
        
    async def send_frame(self,frame):
        print(f"{time.ctime()} - Send frame: {frame}")
        self.writer.write(frame.serialize())
        await self.writer.drain()
    
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
        
    def is_connected(self):
        if self.connection_state == StateConn.set_state('CONNECTED'):
            return True
        return False
    
    
    def set_timeout(self, timeout):
        self.timeout = timeout
        
    def get_connection_info(self):
        return self.ip, self.port, self.connection_state, self.transmission_state, self.timeout
    
    async def check_for_timeouts(self):
        print(f"Starting async check_for_timeouts")
        
        time_now = time.time()
        last_timestamp = self.get_timestamp()
        
        if time_now - last_timestamp > self.timeout_t0:
            print(f'Client {self.ip}:{self.port} timed out and disconnected')
            
            
        if time_now - last_timestamp > self.timeout_t1:
            
            self.set_flag_timeout_t1(1)
            
            # raise TimeoutError(f"Timeout pro t1")
            
        if time_now - last_timestamp > self.timeout_t2:
            if not self.queue.isBlank_send_queue():
                resp = self.queue.generate_s_frame()
                await self.send_frame(resp)
            
        if time_now - last_timestamp > self.timeout_t3:
            frame = self.generate_testdt_act()
            await self.send_frame(frame)
            
            # self.loop.create_task()
        print(f"*******************************")
        print(f"\t {time.time() - last_timestamp}")
        print(f"*******************************")
        print(f"Finish async check_for_timeouts")
    
    
    async def update_state_machine_server(self, fr = 0):
        print(f"Starting async update_state_machine_server")
        
        # set_connection_state()
            # 0 = DISCONNECTED
            # 1 = CONNECTED
        if self.get_connection_state() == 'CONNECTED':
            
        # get_connection_state()
            # 0 = STOPPED
            # 1= WAITING_RUNNING
            # 2 = RUNNING
            # 3 = WAITING_UNCONFIRMED
            # 4 = WAITING_STOPPED
            
            # spravny format pro podminky 
            if fr:
                if isinstance(fr, UFormat):
                    frame = fr.get_type_int()
                
                else:
                    frame = fr.get_type_in_word()   # S-format
            else:
                frame = 0
                
            #* STATE 1 
            if self.get_transmission_state() == 'STOPPED':
                
                
                if frame == acpi.STARTDT_ACT:
                    self.set_transmission_state('RUNNING')
                    new_frame = self.generate_startdt_con()
                    await self.send_frame(new_frame)
                
                # t1_timeout or S-format or I-format   
                if frame == 'S-format' or frame == 'I-format' or \
                    self.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.set_flag_session('ACTIVE_TERMINATION')
                        
            
            #* STATE 2 
            if self.get_transmission_state() == 'RUNNING':
                
                # if frame is stopdt act and send queue is blank
                if frame == acpi.STOPDT_ACT and \
                    self.queue.isBlank_send_queue():
                        
                        # poslat STOPDT CON
                        self.set_transmission_state('STOPPED')
                        new_frame = self.generate_stopdt_con()
                        await self.send_frame(new_frame)
                
                
                # if frame is stopdt act and send queue is not blank
                if frame == acpi.STOPDT_ACT and \
                    not self.queue.isBlank_send_queue():
                        
                        # poslat STOPDT CON
                        self.set_transmission_state('WAITING_UNCONFIRMED')
                
                # t1_timeout    
                if self.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.set_flag_session('ACTIVE_TERMINATION')   
            
            
            #* STATE 3 
            if self.get_transmission_state() == 'WAITING_UNCONFIRMED':
                
                if frame == 'S-format' and \
                    self.queue.isBlank_send_queue():
                        
                        # poslat STOPDT CON
                        self.set_transmission_state('STOPPED')
                        new_frame = self.generate_stopdt_con()
                        await self.send_frame(new_frame)
                
                # t1_timeout or S-format or I-format   
                if frame == 'I-format' or self.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.set_flag_session('ACTIVE_TERMINATION')
            
            
            # default condition if ACTIVE_TERMINATION is set
            if self.get_flag_session() == 'ACTIVE_TERMINATION':
                
                # unset ACTIVE_TERMINATION 
                self.set_flag_session(None)
                
                self.set_transmission_state('STOPPED')
                self.set_connection_state('DISCONNECTED')
                
        else:
            self.set_transmission_state('STOPPED')
            self.set_connection_state('DISCONNECTED')
            
        
        print(f"{self.get_connection_state()}")
        print(f"{self.get_transmission_state()}")
        
        print(f"Finish async update_state_machine_server")
        
    async def update_state_machine_client(self, fr = 0):
        print(f"Starting async update_state_machine_client")
        
        # get_connection_state()
            # 0 = DISCONNECTED
            # 1 = CONNECTED
        if self.get_connection_state() == 'CONNECTED':
            
        # get_connection_state()
            # 0 = STOPPED
            # 1 = WAITING_RUNNING
            # 2 = RUNNING
            # 3 = WAITING_UNCONFIRMED
            # 4 = WAITING_STOPPED
            
            # correct format for next conditions 
            if fr:
                if isinstance(fr, UFormat):
                    frame = fr.get_type_int()
                
                else:
                    frame = fr.get_type_in_word()   # 'S-format'
            else:
                frame = 0
                    
                
            
            #* STATE 1 - 
            if self.get_transmission_state() == 'STOPPED':
                
                # flag for start session is set
                if self.get_flag_session() == 'START_SESSION':
                    
                    # reset flag for start session
                    self.set_flag_session(None)
                    # send start act
                    new_frame = self.generate_startdt_act()
                    await self.send_frame(new_frame)
                    # update state
                    self.set_transmission_state('WAITING_RUNNING')
                
                
                # t1_timeout or S-format or I-format   
                if frame == 'S-format' or frame == 'I-format' or \
                    self.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.set_flag_session('ACTIVE_TERMINATION')
                
            
            #* STATE 2 - 
            if self.get_transmission_state() == 'WAITING_RUNNING':
                
                if frame == acpi.STARTDT_CON:
                    self.set_transmission_state('RUNNING')
                    pass
                
                # t1_timeout or S-format or I-format   
                if frame == 'S-format' or frame == 'I-format' or \
                    self.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.set_flag_session('ACTIVE_TERMINATION')
                        
                
            #* STATE 3 - 
            if self.get_transmission_state() == 'RUNNING':
                
                # To WAITING_STOPPED
                if self.get_flag_session() == 'STOP_SESSION' and \
                    self.queue.isBlank_send_queue():
                        
                        # reset flag for start session
                        self.set_flag_session(None)
                        
                        # send stopdt act
                        new_frame = self.generate_stopdt_act()
                        await self.send_frame(new_frame)
                        # update state
                        self.set_transmission_state('WAITING_STOPPED')
                
                # To WAITING_UNCONFIRMED
                if self.get_flag_session() == 'STOP_SESSION' and \
                    not self.queue.isBlank_send_queue():
                        
                        # reset flag for start session
                        self.set_flag_session(None)
                        
                        # send stopdt act
                        new_frame = self.generate_stopdt_act()
                        await self.send_frame(new_frame)
                        # update state
                        self.set_transmission_state('WAITING_UNCONFIRMED')
                
                # t1_timeout    
                if self.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.set_flag_session('ACTIVE_TERMINATION')
                    
            
            #* STATE 4 
            if self.get_transmission_state() == 'WAITING_UNCONFIRMED':
                
                if frame == acpi.STOPDT_CON:
                    self.set_transmission_state('STOPPED')
                
                if  (frame == 'I-format' or frame == 'S-format' ) and \
                    self.queue.isBlank_send_queue():
                        self.set_transmission_state('WAITING_STOPPED')
                  
                # t1_timeout    
                if self.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.set_flag_session('ACTIVE_TERMINATION')
                    
                    
            #* STATE 5 
            if self.get_transmission_state() == 'WAITING_STOPPED':
                
                if frame == acpi.STOPDT_CON:
                    self.set_transmission_state('STOPPED')
                
                # t1_timeout    
                if self.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.set_flag_session('ACTIVE_TERMINATION')
                 
                    
            # default condition if ACTIVE_TERMINATION is set
            if self.get_flag_session() == 'ACTIVE_TERMINATION':
                
                # unset ACTIVE_TERMINATION 
                self.set_flag_session(None)
                self.set_transmission_state('STOPPED')
                self.set_connection_state('DISCONNECTED')
                   
        else:
            self.set_transmission_state('STOPPED')
            self.set_connection_state('DISCONNECTED')
            
               
        
        print(f"{self.get_connection_state()}")
        print(f"{self.get_transmission_state()}")
        
        print(f"Finish async update_state_machine_client")

    def __del__(self):
        print(f"odstraneni: {self}")
        self.queue.del_session(self)
        
    
    def __enter__(self):
        pass
    def __str__(self):
        return (f"SessionID: {self.id}, ip: {self.ip}, port: {self.port}, connected: {self.is_connected()}")
        pass
        
    def __exit__(*exc_info):
        pass