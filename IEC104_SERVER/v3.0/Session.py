import logging
import asyncio
import time

import acpi
from Frame import Frame
from Parser import Parser
from UFormat import UFormat
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
    _id = 0
    _instances = []
    
    def __init__(self, ip, port, reader, writer,
                 session_params = None, 
                 queue: QueueManager = None,
                 in_queue: IncomingQueueManager = None,
                 out_queue: OutgoingQueueManager = None,
                 packet_buffer: PacketBuffer = None):
        
        self._reader = reader
        self._writer = writer
        self._ip = ip
        self._port = port
        self._timestamp = time.time()
        self._queue = queue
        self._incomming_queue = in_queue
        self._outgoing_queue = out_queue
        self._packet_buffer = packet_buffer
        
        # flag_session = 'START_SESSION'
        # flag_session = 'STOP_SESSION'
        # flag_session = 'ACTIVE_TERMINATION'
        # flag_session = None
        self._flag_session = None 
        
        # flag_timeout_t1 = 0 - good
        # flag_timeout_t1 = 1 - timeout 
        self._flag_timeout_t1 = 0
        
        self._k = session_params[0]
        self._w = session_params[1]
        self._timeout_t0 = session_params[2]
        self._timeout_t1 = session_params[3]
        self._timeout_t2 = session_params[4]
        self._timeout_t3 = session_params[5]
        
        # param for select session
        self._priority = 0
        
        # inical states
        self._connection_state = StateConn.set_state('CONNECTED')
        self._transmission_state = StateTrans.set_state('STOPPED')
        
        
        Session._id += 1
        self._id = Session._id
        Session._instances.append(self)
        
    async def start(self):
        # print(f"Session.start()")
        # self.task_handle_messages = asyncio.create_task(self.handle_messages())
        # self.task_send_frame = asyncio.create_task(self.send_frame())
        # self.task_state = asyncio.create_task(self.update_state_machine_server()) 
        # self.task_timeouts = asyncio.create_task(self.check_for_timeouts())
        # self.task_run = asyncio.create_task(self.runs())
        await self.run()
            
    async def run(self):
        while True:
            
            print(f"run.start()")
            self.task_handle_messages = asyncio.create_task(self.handle_messages())
            self.task_send_frame = asyncio.create_task(self.send_frame())
            self.task_state = asyncio.create_task(self.update_state_machine_server()) 
            self.task_timeouts = asyncio.create_task(self.check_for_timeouts())
            # periodic tasks for session
            # check if client send any data
            
            # třída session si kontroluje zda se nachází data v outgoing_queue
            # pokud ano, vyjme je z fronty, uloží si je do bufferu a pošle klientovi
            # příchozí zprávy zase ukládá do příchozí fronty
            # pokud je příchozí zpráva potvrzením již zaslané, kontroluje a maže zprávu 
            # z bufferu
            resp = await self.task_handle_messages
            if resp:
                print(resp)
                await self.update_state_machine_server(resp)
            await self.task_handle_messages
            await self.task_send_frame
            await self.task_timeouts
            await self.task_state
            # await self.task_run
            
            tasks = await asyncio.all_tasks()
            
            print(f"run.finish()")
            await asyncio.sleep(0.5) # kritický bod pro rychlost aplikace
        
    @property    
    def k(self):
        return self._k
    
    @property
    def w(self):
        return self._w
    
    @property
    def ip(self):
        return self._ip
    
    @property
    def port(self):
        return self._port
    
    @property
    def id(self):
        return self._id
    
    @property
    def flag_session(self):
        return self._flag_session
    
    @flag_session.setter
    def flag_session(self, flag):
        self._flag_session = flag
        
    @property
    def flag_timeout_t1(self):
        return self._flag_timeout_t1
    
    @flag_timeout_t1.setter
    def flag_timeout_t1(self, flag):
        self._flag_timeout_t1 = flag
        
    @property
    def priority(self):
        return self._priority
    
    def add_queue(self, queue):
            self._queue = queue
    
    @property
    def connection_state(self):
        return self._connection_state.get_state()
    
    # 0 = DISCONNECTED
    # 1 = CONNECTED
    @connection_state.setter
    def connection_state(self, state):
        print(f"CHANGE_CONNECTION_STATE: {self._connection_state} -> {state}")
        self._connection_state = StateConn.set_state(state)
    
    
    @property
    def transmission_state(self):
        return self._transmission_state.get_state()
    
    # 0 = STOPPED
    # 1= WAITING_RUNNING
    # 2 = RUNNING
    # 3 = WAITING_UNCONFIRMED
    # 4 = WAITING_STOPPED
    @transmission_state.setter
    def transmission_state(self, state):
        print(f"CHANGE_TRANSMISSION_STATE: {self._transmission_state} -> {state}")
        self._transmission_state = StateTrans.set_state(state)
    
    
        
    @classmethod        # instance s indexem 0 neexistuje ( je rezevrována* )
    def remove_instance(cls, id = 0, instance = None):
        if not id:  # zde rezerva*
            if instance: 
                cls._instances.remove(instance)
                return True
            else:
                return False
        
        if id < len(cls._instances):
            del cls._instances[id]
            return True
        else:
            return False
    def update_timestamp(self):
        print(f"UPDATE_TIMESTAMP: {self._timestamp} -> {time.time()} => Δ={time.time() - self._timestamp}")
        self._timestamp = time.time()
        
    @property
    def timestamp(self):
        return self._timestamp
    
    @timestamp.setter
    def timestamp(self):
        self._timestamp = time.time()
    
    @classmethod
    def get_all_instances(cls):
        return cls._instances
    
    @classmethod
    def get_instance(cls, id: int):
        for inst in cls._instances:
            if inst.id == id:
                return inst
        return None
    
    async def handle_messages(self):
        
        # self.loop = asyncio.get_running_loop()
        try:
            print(f"Starting async handle_messages")
            
            # zde změřit zda timeout nedělá problém zbrždění
            header = await asyncio.wait_for(self._reader.read(2),timeout=0.2)
            
            if header:
                start_byte, frame_length = header
                
                # identifikace IEC 104
                if start_byte == Frame.__start_byte:
                    apdu = await self._reader.read(frame_length)
                    print(f"{time.ctime()} - Received data: {apdu}")
                    if len(apdu) == frame_length:
                        new_apdu = Parser.parser(apdu,frame_length)
                        
                        
                        
                        # if isinstance(new_apdu, UFormat):
                        #     self.loop.create_task(self.handle_U_format(new_apdu))
                        
                        print(f"{time.ctime()} - Receive frame: {new_apdu}")
                        
                        # aktualizace poslední aktivity 
                        self.update_timestamp
                        
                        print(f"Finish async handle_messages.")
                        
                        
                        self._incomming_queue.on_message_received(new_apdu)
                        
                        return new_apdu
            else:
                print(f"doslo k tomuto vubec nekdy?")
                return None
                        
                    
            # přijat nějaký neznámý formát
        except asyncio.TimeoutError:
            print(f'Klient {self} neposlal žádná data.')
            
        except Exception as e:
            print(f"Exception {e}")
    
                
    
    
    ##############################################
    ## RESPONSES
    async def keepalive(self):
        frame = UFormat(acpi.TESTFR_ACT)
        self._writer.write(frame.serialize())
        await self._writer.drain()
        
    ################################################
    ## SEND FRAME
        
    async def send_frame(self,frame: Frame = 0):
        print(f"Start send_frame_task()")
        if frame:
            print(f"{time.ctime()} - Send frame: {frame}")
            self._writer.write(frame.serialize())
            await self._writer.drain()
        else:
            if not self._outgoing_queue.is_Empty():
                frame = await self._outgoing_queue.get_message()
                
                # add to packet buffer
                self._packet_buffer.add_frame(frame.get_ssn(), frame)
                self._writer.write(frame.serialize())
                await self._writer.drain()
        
        
        print(f"Stop send_frame_task()")
        
    async def send_data(self,data):
        print(f"{time.ctime()} - Send data: {data}")
        self._writer.write(data)
        await self._writer.drain()
    
    
        
    @property
    def is_connected(self):
        if self._connection_state == StateConn.set_state('CONNECTED'):
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
        return self._ip, self._port, self._connection_state, self._transmission_state, self._timeout
    
    async def check_for_timeouts(self):
        print(f"Starting async check_for_timeouts")
        
        time_now = time.time()
        last_timestamp = self.timestamp
        
        if time_now - last_timestamp > self._timeout_t0:
            print(f'Client {self._ip}:{self._port} timed out and disconnected')
            
            
        if time_now - last_timestamp > self._timeout_t1:
            
            self.flag_timeout_t1 = 1
            print(f"Timeout t1 is set to 1")
            
            # raise TimeoutError(f"Timeout pro t1")
            
        if time_now - last_timestamp > self._timeout_t2:
            if not self._packet_buffer.is_empty():
                resp = self._queue.generate_s_frame()
                await self.send_frame(resp)
            
        if time_now - last_timestamp > self._timeout_t3:
            frame = self._queue.generate_testdt_act()
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
            if self.connection_state == 'CONNECTED':
                
            # get_connection_state()
                # 0 = STOPPED
                # 1= WAITING_RUNNING
                # 2 = RUNNING
                # 3 = WAITING_UNCONFIRMED
                # 4 = WAITING_STOPPED
                
                # spravny format pro podminky 
                if fr:
                    if isinstance(fr, UFormat):
                        frame = fr._type_int()
                    
                    else:
                        frame = fr.get_type_in_word()   # S-format
                else:
                    frame = 0
                    
                actual_transmission_state = self.transmission_state
                
                # timeout t1
                if not self.flag_timeout_t1:
                    
                
                    #* STATE 1 
                    if actual_transmission_state == 'STOPPED':
                        
                        
                        if frame == acpi.STARTDT_ACT:
                            self.transmission_state = 'RUNNING'
                            new_frame = self._queue.generate_startdt_con()
                            await self.send_frame(new_frame)
                        
                        # t1_timeout or S-format or I-format   
                        if frame == 'S-format' or frame == 'I-format':
                                self.flag_session = 'ACTIVE_TERMINATION'
                                
                    
                    #* STATE 2 
                    if actual_transmission_state == 'RUNNING':
                        
                        # if frame is stopdt act and send queue is blank
                        if frame == acpi.STOPDT_ACT and \
                            self._packet_buffer.is_empty():
                                
                                # poslat STOPDT CON
                                self.transmission_state = 'STOPPED'
                                new_frame = self._queue.generate_stopdt_con()
                                await self.send_frame(new_frame)
                        
                        
                        # if frame is stopdt act and send queue is not blank
                        if frame == acpi.STOPDT_ACT and \
                            not self._packet_buffer.is_empty():
                                
                                # poslat STOPDT CON
                                self.transmission_state = 'WAITING_UNCONFIRMED'
                        
                    
                    #* STATE 3 
                    if actual_transmission_state == 'WAITING_UNCONFIRMED':
                        
                        if frame == 'S-format' and \
                            self._packet_buffer.is_empty():
                                
                                # poslat STOPDT CON
                                self.transmission_state('STOPPED')
                                new_frame = self._queue.generate_stopdt_con()
                                await self.send_frame(new_frame)
                        
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
                    
            else:
                self.transmission_state = 'STOPPED'
                self.connection_state = 'DISCONNECTED'
                
            
            print(f"{self.connection_state}")
            print(f"{actual_transmission_state}")
            
            await asyncio.sleep(0.5)
            print(f"Finish async update_state_machine_server")
            
    async def update_state_machine_client(self, fr = 0):
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
                
                # correct format for next conditions 
                if fr:
                    if isinstance(fr, UFormat):
                        frame = fr._type_int()
                    
                    else:
                        frame = fr.get_type_in_word()   # 'S-format'
                else:
                    frame = 0
                        
                actual_transmission_state = self.transmission_state   
                
                #* STATE 1 - 
                if actual_transmission_state == 'STOPPED':
                    
                    # flag for start session is set
                    if self.flag_session == 'START_SESSION':
                        
                        # reset flag for start session
                        self.flag_session = None
                        # send start act
                        new_frame = self._queue.generate_startdt_act()
                        await self.send_frame(new_frame)
                        # update state
                        self.transmission_state = 'WAITING_RUNNING'
                    
                    
                    # t1_timeout or S-format or I-format   
                    if frame == 'S-format' or frame == 'I-format' or \
                        self.flag_timeout_t1:
                            
                            # reset flag for t1_timeout
                            self.flag_timeout_t1 = 0
                            # aktivni ukonceni
                            self.flag_session = 'ACTIVE_TERMINATION'
                    
                
                #* STATE 2 - 
                if actual_transmission_state == 'WAITING_RUNNING':
                    
                    if frame == acpi.STARTDT_CON:
                        self.transmission_state = 'RUNNING'
                    
                    # t1_timeout or S-format or I-format   
                    if frame == 'S-format' or frame == 'I-format' or \
                        self.flag_timeout_t1:
                            
                            # reset flag for t1_timeout
                            self.flag_timeout_t1 = 0
                            # aktivni ukonceni
                            self.flag_session = 'ACTIVE_TERMINATION'
                            
                    
                #* STATE 3 - 
                if actual_transmission_state == 'RUNNING':
                    
                    # To WAITING_STOPPED
                    if self.flag_session == 'STOP_SESSION' and \
                        self._packet_buffer.is_empty():
                            
                            # reset flag for start session
                            self.flag_session = None
                            
                            # send stopdt act
                            new_frame = self._queue.generate_stopdt_act()
                            await self.send_frame(new_frame)
                            # update state
                            self.transmission_state = 'WAITING_STOPPED'
                    
                    # To WAITING_UNCONFIRMED
                    if self.flag_session == 'STOP_SESSION' and \
                        not self._packet_buffer.is_empty():
                            
                            # reset flag for start session
                            self.flag_session = None
                            
                            # send stopdt act
                            new_frame = self._queue.generate_stopdt_act()
                            await self.send_frame(new_frame)
                            # update state
                            self.transmission_state = 'WAITING_UNCONFIRMED'
                    
                    # t1_timeout    
                    if self.flag_timeout_t1:
                        
                        # reset flag for t1_timeout
                        self.flag_timeout_t1 = 0
                        # aktivni ukonceni
                        self.flag_session = 'ACTIVE_TERMINATION'
                        
                
                #* STATE 4 
                if actual_transmission_state == 'WAITING_UNCONFIRMED':
                    
                    if frame == acpi.STOPDT_CON:
                        self.transmission_state = 'STOPPED'
                    
                    if  (frame == 'I-format' or frame == 'S-format' ) and \
                        self._packet_buffer.is_empty():
                            self.transmission_state = 'WAITING_STOPPED'
                    
                    # t1_timeout    
                    if self.flag_timeout_t1:
                        
                        # reset flag for t1_timeout
                        self.flag_timeout_t1 = 0
                        # aktivni ukonceni
                        self.flag_session = 'ACTIVE_TERMINATION'
                        
                        
                #* STATE 5 
                if actual_transmission_state == 'WAITING_STOPPED':
                    
                    if frame == acpi.STOPDT_CON:
                        self.transmission_state = 'STOPPED'
                    
                    # t1_timeout    
                    if self.flag_timeout_t1:
                        
                        # reset flag for t1_timeout
                        self.flag_timeout_t1 = 0
                        # aktivni ukonceni
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
            
            await asyncio.sleep(0.5)
            print(f"Finish async update_state_machine_client")

    
    def __del__(self):
        print(f"odstraneni: {self}")
        if self:
            return self._queue.del_session(self)
        return False
    
    def __enter__(self):
        pass
    def __str__(self):
        return (f"SessionID: {self._id}, ip: {self._ip}, port: {self._port}, connected: {self.is_connected}")
        pass
        
    def __exit__(*exc_info):
        pass