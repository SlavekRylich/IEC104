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
        
        # flag_session = 'start_session'
        # flag_session = 'stop_session'
        # flag_session = 'active_termination'
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
        
        self.connection_state = StateConn.set_state('Connected')
        self.transmission_state = StateTrans.set_state('Stopped')
        
        
        Session.id += 1
        self.id = Session.id
        Session.instances.append(self)
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
    
    # 0 = Disconnected
    # 1 = Connected
    def set_connection_state(self, state):
        self.connection_state = state
    
    # 0 = Stopped
    # 1= Waiting_running
    # 2 = Running
    # 3 = Waiting_unconfirmed
    # 4 = Waiting_stopped
    def set_transmission_state(self, state):
        self.transmission_state = state
    
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
        
    
        
    async def check_for_message(self):
        if self.connection_state == StateConn.set_state('Connected'):
                await self.handle_messages()
            
    async def handle_messages(self):
        
        self.loop = asyncio.get_running_loop()
        try:
            while True:
                print(f"Starting async handle_messages")
                
                header = await asyncio.wait_for(self.reader.read(2),timeout=0.5)
                
                if not header:
                    return None
                
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
                        
                        print(f"Finish async handle_messages.")
                        return new_apdu
                        
                    
            # přijat nějaký neznámý formát
        except asyncio.TimeoutError:
            print(f'Klient {self.ip} neposlal žádná data.')
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
    
    
    ##############################################
    ## RESPONSES
    async def keepalive(self):
        frame = UFormat(acpi.TESTFR_ACT)
        self.writer.write(frame.serialize())
        await self.writer.drain()
        
    ################################################
    ## SEND FRAME
        
    async def send_frame(self,frame):
        self.writer.write(frame.serialize())
        await self.writer.drain()
    
    ################################################
    # GENERATE U FRAME
    
    async def generate_testdt_act(self):
        return UFormat(acpi.TESTFR_ACT)
    
    async def generate_testdt_con(self):
        return UFormat(acpi.TESTFR_CON)
    
    async def generate_startdt_act(self):
        return UFormat(acpi.STARTDT_ACT)
    
    async def generate_startdt_con(self):
        return UFormat(acpi.STARTDT_CON)
        
    async def generate_stopdt_act(self):
        return UFormat(acpi.STOPDT_ACT)
        
    async def generate_stopdt_con(self):
        return UFormat(acpi.STOPDT_CON)
        
    def is_connected(self):
        if self.connection_state == StateConn.set_state('Connected'):
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
            
            self.set_transmission_state('Stopped')
            self.set_connection_state('Disconnected')
            
            raise Exception(f"Timeout pro t1")
            
        if time_now - last_timestamp > self.timeout_t2:
            resp = self.queue.response_S_format()
            await self.send_frame(resp)
            
        if time_now - last_timestamp > self.timeout_t3:
            await self.response_testdt_act()
            # self.loop.create_task()
        
        print(f"Finish async check_for_timeouts")
    
    
    async def update_state_machine_server(self, fr = 0):
        print(f"Starting async update_state_machine")
        
        # set_connection_state()
            # 0 = Disconnected
            # 1 = Connected
        if self.get_connection_state() == 'Connected':
            
        # get_connection_state()
            # 0 = Stopped
            # 1= Waiting_running
            # 2 = Running
            # 3 = Waiting_unconfirmed
            # 4 = Waiting_stopped
            
            # spravny format pro podminky 
            if isinstance(fr, UFormat):
                frame = fr.get_type_int()
            
            else:
                frame = fr.get_type_in_word()   # S-format
            
            #* STATE 1 
            if self.get_transmission_state() == 'Stopped':
                
                
                if frame == acpi.STARTDT_ACT:
                    self.set_transmission_state('Running')
                    await self.response_startdt_con()
                
                # t1_timeout or S-format or I-format   
                if frame == 'S-format' or frame == 'I-format' or \
                    self.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.set_flag_session('active_termination')
                        
            
            #* STATE 2 
            if self.get_transmission_state() == 'Running':
                
                # if frame is stopdt act and send queue is blank
                if frame == acpi.STOPDT_ACT and \
                    self.queue.isBlank_send_queue():
                        
                        # poslat STOPDT CON
                        self.set_transmission_state('Stopped')
                        await self.response_stopdt_con()
                
                
                # if frame is stopdt act and send queue is not blank
                if frame == acpi.STOPDT_ACT and \
                    not self.queue.isBlank_send_queue():
                        
                        # poslat STOPDT CON
                        self.set_transmission_state('Waiting_unconfirmed')
                
                # t1_timeout    
                if self.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.set_flag_session('active_termination')   
            
            
            #* STATE 3 
            if self.get_transmission_state() == 'Waiting_unconfirmed':
                
                if frame.get_type_in_word() == 'S-format' and \
                    self.queue.isBlank_send_queue():
                        
                        # poslat STOPDT CON
                        self.set_transmission_state('Stopped')
                        await self.response_stopdt_con()
                
                # t1_timeout or S-format or I-format   
                if frame == 'I-format' or self.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.set_flag_session('active_termination')
            
            
            # default condition if active_termination is set
            if self.get_flag_session() == 'active_termination':
                
                # unset active_termination 
                self.set_flag_session(None)
                
                self.set_transmission_state('Stopped')
                self.set_connection_state('Disconnected')
                del self
                
        else:
            self.set_transmission_state('Stopped')
            self.set_connection_state('Disconnected')
            pass
        
        print(f"Finish async update_state_machine")
        
    async def update_state_machine_client(self, fr = 0):
        print(f"Starting async update_state_machine")
        
        # get_connection_state()
            # 0 = Disconnected
            # 1 = Connected
        if self.get_connection_state('Connected'):
            
        # get_connection_state()
            # 0 = Stopped
            # 1 = Waiting_running
            # 2 = Running
            # 3 = Waiting_unconfirmed
            # 4 = Waiting_stopped
            
            # correct format for next conditions 
            if isinstance(fr, UFormat):
                frame = fr.get_type_int()
            
            else:
                frame = fr.get_type_in_word()   # 'S-format'
                
                
            
            #* STATE 1 - 
            if self.get_transmission_state() == 'Stopped':
                
                # flag for start session is set
                if self.get_flag_session() == 'start_session':
                    
                    # reset flag for start session
                    self.set_flag_session(None)
                    # send start act
                    await self.response_startdt_act()
                    # update state
                    self.set_transmission_state('Waiting_running')
                
                
                # t1_timeout or S-format or I-format   
                if frame == 'S-format' or frame == 'I-format' or \
                    self.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.set_flag_session('active_termination')
                
            
            #* STATE 2 - 
            if self.get_transmission_state() == 'Waiting_running':
                
                if frame == acpi.STARTDT_CON:
                    self.set_transmission_state('Running')
                    pass
                
                # t1_timeout or S-format or I-format   
                if frame == 'S-format' or frame == 'I-format' or \
                    self.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.set_flag_session('active_termination')
                        
                
            #* STATE 3 - 
            if self.get_transmission_state() == 'Running':
                
                # To pending_stopped
                if self.get_flag_session() == 'stop_session' and \
                    self.queue.isBlank_send_queue():
                        
                        # reset flag for start session
                        self.set_flag_session(None)
                        # send start act
                        await self.response_stopdt_act()
                        # update state
                        self.set_transmission_state('Waiting_stopped')
                
                # To pending_unconfirmed
                if self.get_flag_session() == 'stop_session' and \
                    not self.queue.isBlank_send_queue():
                        
                        # reset flag for start session
                        self.set_flag_session(None)
                        # send start act
                        await self.response_stopdt_act()
                        # update state
                        self.set_transmission_state('Waiting_unconfirmed')
                
                # t1_timeout    
                if self.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.set_flag_session('active_termination')
                    
            
            #* STATE 4 
            if self.get_transmission_state() == 'Waiting_unconfirmed':
                
                if frame == acpi.STOPDT_CON:
                    self.set_transmission_state('Stopped')
                
                if  (frame == 'I-format' or frame == 'S-format' ) and \
                    self.queue.isBlank_send_queue():
                        self.set_transmission_state('Waiting_stopped')
                  
                # t1_timeout    
                if self.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.set_flag_session('active_termination')
                    
                    
            #* STATE 5 
            if self.get_transmission_state() == 'Waiting_stopped':
                
                if frame == acpi.STOPDT_CON:
                    self.set_transmission_state('Stopped')
                
                # t1_timeout    
                if self.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.set_flag_session('active_termination')
                 
                    
            # default condition if active_termination is set
            if self.get_flag_session() == 'active_termination':
                
                # unset active_termination 
                self.set_flag_session(None)
                self.set_transmission_state('Stopped')
                self.set_connection_state('Disconnected')
                del self
                   
        else:
            self.set_transmission_state('Stopped')
            self.set_connection_state('Disconnected')
            pass
        
        print(f"Finish async update_state_machine")

    def __del__(self):
        self.queue.del_session(self)
        
    
    def __enter__(self):
        pass
    def __str__(self):
        return (f"SessionID: {self.id}, ip: {self.ip}, port: {self.port}, connected: {self.is_connected()}")
        pass
        
    def __exit__(*exc_info):
        pass