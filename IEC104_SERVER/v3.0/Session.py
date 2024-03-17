import logging
import asyncio
import time


import acpi
from Frame import Frame
from Parser import Parser
from UFormat import UFormat
from IFormat import IFormat
from State import StateConn,StateTrans
from IncomingQueueManager import IncomingQueueManager
from OutgoingQueueManager import OutgoingQueueManager
from Packet_buffer import PacketBuffer
from QueueManager import QueueManager

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

class Session:
    """Class for session.
    """
    # třídní proměná pro uchování unikátní id každé instance
    __id = 0
    __instances = []
    
    def __init__(self, ip, port, reader, writer,
                 session_params = None, 
                 queue: QueueManager = None,
                 in_queue: IncomingQueueManager = None,
                 out_queue: OutgoingQueueManager = None,
                 packet_buffer: PacketBuffer = None,
                 whoami = 'client'):
        
        self.__reader = reader
        self.__writer = writer
        self.__ip = ip
        self.__port = port
        self.__timestamp = time.time()
        self.__queue = queue
        self.__incomming_queue = in_queue
        self.__outgoing_queue = out_queue
        self.__packet_buffer = packet_buffer
        
        self.__whoami = whoami
        
        self.__local_queue = asyncio.Queue(maxsize=256)
        
        # timing
        self.__async_time = 0.5
        self.__task_timeouts_time = 1
        
        # flag_session = 'START_SESSION'
        # flag_session = 'STOP_SESSION'
        # flag_session = 'ACTIVE_TERMINATION'
        # flag_session = None
        self.__flag_session = None 
        
        # flag_timeout_t1 = 0 - good
        # flag_timeout_t1 = 1 - timeout 
        self.__flag_timeout_t1 = 0
        
        self.__k = session_params[0]
        self.__w = session_params[1]
        self.__timeout_t0 = session_params[2]
        self.__timeout_t1 = session_params[3]
        self.__timeout_t2 = session_params[4]
        self.__timeout_t3 = session_params[5]
        
        # param for select session
        self.__priority = 0
        
        # inical states
        self.__connection_state = StateConn.set_state('CONNECTED')
        self.__transmission_state = StateTrans.set_state('STOPPED')
        
        
        self.__task_handle_messages = asyncio.create_task(self.handle_messages())
        self.__task_send_frame = asyncio.create_task(self.send_frame())
        
        if self.__whoami == 'server':
            self.__task_state = asyncio.create_task(self.update_state_machine_server()) 
        else:
            self.__task_state = asyncio.create_task(self.update_state_machine_client())
            
        self.__task_timeouts = asyncio.create_task(self.check_for_timeouts())
        
        Session.__id += 1
        self.__id = Session.__id
        Session.__instances.append(self)
        
        
    async def start(self):
        
        while True:
            print(f"Session.start() - toto se vypise pouze jednou.")
            await asyncio.gather(self.__task_handle_messages,
                                 self.__task_send_frame,
                                 self.__task_state,
                                 self.__task_timeouts)
            # if self.__tasks:
            #     await asyncio.gather(*(task for task in self.__tasks))
            
            await asyncio.sleep(self.__async_time)
     
    @property    
    def k(self):
        return self.__k
    
    @property
    def w(self):
        return self.__w
    
    @property
    def ip(self):
        return self.__ip
    
    @property
    def port(self):
        return self.__port
    
    @property
    def id(self):
        return self.__id
    
    @property
    def flag_session(self):
        return self.__flag_session
    
    @flag_session.setter
    def flag_session(self, flag):
        self.__flag_session = flag
        
    @property
    def flag_timeout_t1(self):
        return self.__flag_timeout_t1
    
    @flag_timeout_t1.setter
    def flag_timeout_t1(self, flag):
        self.__flag_timeout_t1 = flag
        
    @property
    def priority(self):
        return self.__priority
    
    def add_queue(self, queue):
            self.__queue = queue
    
    @property
    def connection_state(self):
        return self.__connection_state.get_state()
    
    # 0 = DISCONNECTED
    # 1 = CONNECTED
    @connection_state.setter
    def connection_state(self, state):
        print(f"CHANGE_CONNECTION_STATE: {self.__connection_state} -> {state}")
        self.__connection_state = StateConn.set_state(state)
    
    
    @property
    def transmission_state(self):
        return self.__transmission_state.get_state()
    
    # 0 = STOPPED
    # 1= WAITING_RUNNING
    # 2 = RUNNING
    # 3 = WAITING_UNCONFIRMED
    # 4 = WAITING_STOPPED
    @transmission_state.setter
    def transmission_state(self, state):
        print(f"CHANGE_TRANSMISSION_STATE: {self.__transmission_state} -> {state}")
        self.__transmission_state = StateTrans.set_state(state)
    
    
        
    @classmethod        # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id = 0, instance = None):
        if not id:  # zde rezerva*
            if instance: 
                cls.__instances.remove(instance)
                return True
            else:
                return False
        
        if id < len(cls.__instances):
            del cls.__instances[id]
            return True
        else:
            return False
        
    def update_timestamp(self):
        print(f"UPDATE_TIMESTAMP: {self.__timestamp} -> {time.time()} => Δ={time.time() - self.__timestamp}")
        self.__timestamp = time.time()
        
    @property
    def timestamp(self):
        return self.__timestamp
    
    @timestamp.setter
    def timestamp(self):
        self.__timestamp = time.time()
    
    @classmethod
    def get_all_instances(cls):
        return cls.__instances
    
    @classmethod
    def get_instance(cls, id: int):
        for inst in cls.__instances:
            if inst.id == id:
                return inst
        return None
    
    async def handle_messages(self):
        while True:
            await asyncio.sleep(self.__async_time) # kritický bod pro rychlost ap    
            # self.loop = asyncio.get_running_loop()
            try:
                print(f"Starting async handle_messages")
                
                # zde změřit zda timeout nedělá problém zbrždění
                header = await asyncio.wait_for(self.__reader.read(2),timeout=0.2)
                
                if header:
                    start_byte, frame_length = header
                    
                    # identifikace IEC 104
                    if start_byte == Frame._start_byte:
                        apdu = await self.__reader.read(frame_length)
                        if len(apdu) == frame_length:
                            new_apdu = Parser.parser(apdu,frame_length)
                            
                            
                            print(f"{time.ctime()} - Receive frame: {new_apdu}")
                            
                            # aktualizace poslední aktivity 
                            self.update_timestamp()
                            
                            await self.__incomming_queue.on_message_received(new_apdu)
                            self.__local_queue.put_nowait(new_apdu)
                            
                            print(f"Finish async handle_messages.")
                            
                            # return new_apdu
                else:
                    print(f"zadne prichozi zpravy")
                    
                            
                        
                # přijat nějaký neznámý formát
            except asyncio.TimeoutError:
                print(f'Klient {self} neposlal žádná data.')
                
            except Exception as e:
                print(f"Exception {e}")
        
    
    
    ##############################################
    ## RESPONSES
    async def keepalive(self):
        frame = UFormat(acpi.TESTFR_ACT)
        self.__writer.write(frame.serialize())
        await self.__writer.drain()
        
    ################################################
    ## SEND FRAME
        
    async def send_frame(self,frame: Frame = 0):
        while True:
            try:
                await asyncio.sleep(self.__async_time) # kritický bod pro rychlost ap    
                print(f"Start send_frame_task()")
                # print("\x1b[31mToto je červený text.\x1b[0m")
                if frame:
                    print(f"{time.ctime()} - Send frame: {frame}")
                    self.__writer.write(frame.serialize())
                    await self.__writer.drain()
                else:
                    
                        if not self.__outgoing_queue.is_Empty():
                            print(f"posílá se neco z odchozí fronty")
                            frame = await self.__outgoing_queue.get_message()
                            
                            print(f"{time.ctime()} - Send frame: {frame}")
                            self.__writer.write(frame.serialize())
                            await self.__writer.drain()
                   
                # add to packet buffer
                if isinstance(frame, IFormat):
                    self.__packet_buffer.add_frame(frame.ssn, frame)  
                          
            except asyncio.QueueEmpty:
                print(f"problem v asynciu")
            except Exception as e:
                print(f"Exception {e}")
            
            print(f"Stop send_frame_task()")
        
    async def send_data(self,data):
        print(f"{time.ctime()} - Send data: {data}")
        self.__writer.write(data)
        await self.__writer.drain()
    
    
        
    @property
    def is_connected(self):
        if self.__connection_state == StateConn.set_state('CONNECTED'):
            return True
        return False
    
    
    @property
    def timeout(self):
        return self._timeout
    @timeout.setter
    def timeout(self, timeout):
        self._timeout = timeout
        
    async def on_connection_lost(self):
        pass
        
    @property
    def connection_info(self):
        return self.__ip, self.__port, self.__connection_state, self.__transmission_state, self._timeout
    
    async def check_for_timeouts(self):
        while True:
            await asyncio.sleep(self.__task_timeouts_time) # kritický bod pro rychlost ap    
            print(f"Starting async check_for_timeouts")
            
            time_now = time.time()
            last_timestamp = self.timestamp
            
            if time_now - last_timestamp > self.__timeout_t0:
                print(f'Client {self.__ip}:{self.__port} timed out and disconnected')
                
                
            if time_now - last_timestamp > self.__timeout_t1:
                
                self.flag_timeout_t1 = 1
                print(f"Timeout t1 is set to 1")
                
                # raise TimeoutError(f"Timeout pro t1")
                
            if time_now - last_timestamp > self.__timeout_t2:
                if not self.__packet_buffer.is_empty():
                    resp = self.__queue.generate_s_frame()
                    await self.__outgoing_queue.to_send(resp)
                
            if time_now - last_timestamp > self.__timeout_t3:
                frame = self.__queue.generate_testdt_act()
                await self.__outgoing_queue.to_send(frame)
                
                # self.loop.create_task()
            print(f"*******************************")
            print(f"\t {time.time() - last_timestamp}")
            print(f"*******************************")
            print(f"Finish async check_for_timeouts")
        
    
    async def update_state_machine_server(self, fr: Frame = 0):
        while True:
            try:
                await asyncio.sleep(self.__async_time) # kritický bod pro rychlost
                print(f"Starting async update_state_machine_server")
                
                # set_connection_state()
                    # 0 = DISCONNECTED
                    # 1 = CONNECTED
                if self.connection_state == 'CONNECTED':
                    
                # get_connection_state()
                    # 0 = STOPPED
                    # 1= WAITING_RUNNING
                    # 2 = RUNNING
                    # 3 = WAITING_UNCONFIRMED
                    # 4 = WAITING_STOPPED
                    
                    if not self.__local_queue.empty():
                        fr = self.__local_queue.get_nowait()
                        print(f"použit z lokalni fronty pro update: {fr}")
                    
                    # spravny format pro podminky 
                    if fr:
                        if isinstance(fr, UFormat):
                            frame = fr.type_int
                        
                        else:
                            frame = fr.type_in_word   # S-format
                    else:
                        frame = 0
                        
                    actual_transmission_state = self.transmission_state
                    
                    # timeout t1
                    if not self.flag_timeout_t1:
                        
                    
                        #* STATE 1 
                        if actual_transmission_state == 'STOPPED':
                            
                            if frame == acpi.STARTDT_ACT:
                                self.transmission_state = 'RUNNING'
                                new_frame = self.__queue.generate_startdt_con()
                                await self.__outgoing_queue.to_send(new_frame)
                            
                            # S-format or I-format   
                            if frame == 'S-format' or frame == 'I-format':
                                    self.flag_session = 'ACTIVE_TERMINATION'
                                    
                        
                        #* STATE 2 
                        if actual_transmission_state == 'RUNNING':
                            
                            # if frame is stopdt act and send queue is blank
                            if frame == acpi.STOPDT_ACT and \
                                self.__packet_buffer.is_empty():
                                    
                                    # poslat STOPDT CON
                                    self.transmission_state = 'STOPPED'
                                    new_frame = self.__queue.generate_stopdt_con()
                                    await self.__outgoing_queue.to_send(new_frame)
                            
                            
                            # if frame is stopdt act and send queue is not blank
                            if frame == acpi.STOPDT_ACT and \
                                not self.__packet_buffer.is_empty():
                                    
                                    # poslat STOPDT CON
                                    self.transmission_state = 'WAITING_UNCONFIRMED'
                            
                        
                        #* STATE 3 
                        if actual_transmission_state == 'WAITING_UNCONFIRMED':
                            
                            if frame == 'S-format' and \
                                self.__packet_buffer.is_empty():
                                    
                                    # poslat STOPDT CON
                                    self.transmission_state('STOPPED')
                                    new_frame = self.__queue.generate_stopdt_con()
                                    await self.__outgoing_queue.to_send(new_frame)
                            
                            # t1_timeout or S-format or I-format   
                            if frame == 'I-format':
                                self.flag_session('ACTIVE_TERMINATION')
                    
                    else:
                        # reset flag_timeout_t1
                        self.flag_timeout_t1 = 0
                        print(f"Timeout t1 is set to 0")
                        self.flag_session = 'ACTIVE_TERMINATION'    
                    
                    # default condition if ACTIVE_TERMINATION is set
                    if self.flag_session == 'ACTIVE_TERMINATION':
                        
                        # unset ACTIVE_TERMINATION 
                        self.flag_session = None
                        
                        self.transmission_state = 'STOPPED'
                        self.connection_state = 'DISCONNECTED'
                        
                        # zde vyvolat odstranění session
                        
                        
                else:
                    self.transmission_state = 'STOPPED'
                    self.connection_state = 'DISCONNECTED'
                    
                
                print(f"{self.connection_state}")
                print(f"{actual_transmission_state}")
                
                await asyncio.sleep(self.__async_time)
                print(f"Finish async update_state_machine_server")
                
            except Exception as e:
                print(f"Exception {e}")
                
    async def update_state_machine_client(self, fr: Frame = 0):
        while True:
            
            print(f"Starting async update_state_machine_client")
            
            # get_connection_state()
                # 0 = DISCONNECTED
                # 1 = CONNECTED
            if self.connection_state == 'CONNECTED':
                
            # get_connection_state()
                # 0 = STOPPED
                # 1 = WAITING_RUNNING
                # 2 = RUNNING
                # 3 = WAITING_UNCONFIRMED
                # 4 = WAITING_STOPPED
                
                if not self.__local_queue.empty():
                    fr = self.__local_queue.get_nowait()
                    print(f"použit z lokalni fronty pro update: {fr}")
                
                # correct format for next conditions 
                if fr:
                    if isinstance(fr, UFormat):
                        frame = fr.type_int
                    
                    else:
                        frame = fr.type_in_word   # 'S-format'
                else:
                    frame = 0
                     
                
                # timeout t1
                if not self.flag_timeout_t1:
                   
                    actual_transmission_state = self.transmission_state   
                    
                    #* STATE 1 - 
                    if actual_transmission_state == 'STOPPED':
                        
                        # flag for start session is set
                        if self.flag_session == 'START_SESSION':
                            
                            # reset flag for start session
                            self.flag_session = None
                            # send start act
                            new_frame = self.__queue.generate_startdt_act()
                            await self.__outgoing_queue.to_send(new_frame)
                            # update state
                            self.transmission_state = 'WAITING_RUNNING'
                        
                        
                        # t1_timeout or S-format or I-format   
                        if frame == 'S-format' or frame == 'I-format':
                                
                                # aktivni ukonceni
                                self.flag_session = 'ACTIVE_TERMINATION'
                        
                    
                    #* STATE 2 - 
                    if actual_transmission_state == 'WAITING_RUNNING':
                        
                        if frame == acpi.STARTDT_CON:
                            self.transmission_state = 'RUNNING'
                        
                        # t1_timeout or S-format or I-format   
                        if frame == 'S-format' or frame == 'I-format':
                                
                                # aktivni ukonceni
                                self.flag_session = 'ACTIVE_TERMINATION'
                                
                        
                    #* STATE 3 - 
                    if actual_transmission_state == 'RUNNING':
                        
                        # To WAITING_STOPPED
                        if self.flag_session == 'STOP_SESSION' and \
                            self.__packet_buffer.is_empty():
                                
                                # reset flag for start session
                                self.flag_session = None
                                
                                # send stopdt act
                                new_frame = self.__queue.generate_stopdt_act()
                                await self.__outgoing_queue.to_send(new_frame)
                                # update state
                                self.transmission_state = 'WAITING_STOPPED'
                        
                        # To WAITING_UNCONFIRMED
                        if self.flag_session == 'STOP_SESSION' and \
                            not self.__packet_buffer.is_empty():
                                
                                # reset flag for start session
                                self.flag_session = None
                                
                                # send stopdt act
                                new_frame = self.__queue.generate_stopdt_act()
                                await self.__outgoing_queue.to_send(new_frame)
                                # update state
                                self.transmission_state = 'WAITING_UNCONFIRMED'
                                                    
                    
                    #* STATE 4 
                    if actual_transmission_state == 'WAITING_UNCONFIRMED':
                        
                        if frame == acpi.STOPDT_CON:
                            self.transmission_state = 'STOPPED'
                        
                        if  (frame == 'I-format' or frame == 'S-format' ) and \
                            self.__packet_buffer.is_empty():
                                self.transmission_state = 'WAITING_STOPPED'
                        
                            
                    #* STATE 5 
                    if actual_transmission_state == 'WAITING_STOPPED':
                        
                        if frame == acpi.STOPDT_CON:
                            self.transmission_state = 'STOPPED'
                        
                else:
                    # reset flag_timeout_t1
                    self.flag_timeout_t1 = 0
                    print(f"Timeout t1 is set to 0")
                    self.flag_session = 'ACTIVE_TERMINATION'            
                        
                # default condition if ACTIVE_TERMINATION is set
                if self.flag_session == 'ACTIVE_TERMINATION':
                    
                    # unset ACTIVE_TERMINATION 
                    self.flag_session = None
                    self.transmission_state = 'STOPPED'
                    self.connection_state = 'DISCONNECTED'
                    
            else:
                self.transmission_state = 'STOPPED'
                self.connection_state = 'DISCONNECTED'
                
                
            
            print(f"{self.connection_state}")
            print(f"{actual_transmission_state}")
            
            await asyncio.sleep(self.__async_time)
            print(f"Finish async update_state_machine_client")

    
    def __del__(self):
        print(f"odstraneni: {self}")
        if self:
            return self.__queue.del_session(self)
        return False
    
    def __enter__(self):
        pass
    def __str__(self):
        return (f"SessionID: {self.__id}, ip: {self.__ip}, port: {self.__port}, connected: {self.is_connected}")
        pass
        
    def __exit__(*exc_info):
        pass