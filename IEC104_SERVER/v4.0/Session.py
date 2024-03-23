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
from Timeout import Timeout

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
    
    def __init__(self, 
                 ip,
                 port,
                 reader,
                 writer,
                 session_params = None, 
                 queue: QueueManager = None,
                 whoami = 'client'):
        
        # features of session
        self.__reader = reader
        self.__writer = writer
        self.__ip = ip
        self.__port = port
        
        self.__event_in = queue.event_in
        self.__event_out = queue.event_out
        self.__event_update = asyncio.Event()
        
        
        # Queues 
        self.__queue = queue
        self.__incomming_queue = queue.in_queue
        self.__outgoing_queue = queue.out_queue
        self.__send_buffer = queue.send_buffer
        self.__recv_buffer = queue.recv_buffer
        
        # server / client
        self.__whoami = whoami
        
        # local queue is for handle message to update_state_machine
        self.__local_queue = asyncio.Queue(maxsize=256)
        
        
        # flag_session = 'START_SESSION'
        # flag_session = 'STOP_SESSION'
        # flag_session = 'ACTIVE_TERMINATION'
        # flag_session = None
        self.__flag_session = None 
        
        # flag_timeout_t1 = 0 - good
        # flag_timeout_t1 = 1 - timeout 
        self.__flag_timeout_t1 = 0
        
        
        # flag for delete self
        self.__flag_delete = False
        
        # Parameters from config file
        self.__k = session_params[0]
        self.__w = session_params[1]
        self.__timeout_t0 = session_params[2]
        self.__timeout_t1 = session_params[3]
        self.__timeout_t2 = session_params[4]
        self.__timeout_t3 = session_params[5]
        
        
        # timing of tasks
        self.__async_time = 0.5
        self.__time_for_task_timeouts = 0.8
        
        # timeouts
        self.__timestamp_t0 = Timeout(self.__timeout_t0)
        self.__timestamp_t1 = Timeout(self.__timeout_t1)
        self.__timestamp_t2 = Timeout(self.__timeout_t2)
        self.__timestamp_t3 = Timeout(self.__timeout_t3)
        
        
        # param for select session
        self.__priority = 0
        
        # inical states
        self.__connection_state = StateConn.set_state('CONNECTED')
        self.__transmission_state = StateTrans.set_state('STOPPED')
        
        # Tasks
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
        
        # while True:
            print(f"Session.start() - toto se vypise pouze jednou.")
            await asyncio.gather(self.__task_handle_messages,
                                 self.__task_send_frame,
                                 self.__task_state,
                                 self.__task_timeouts)
            # if self.__tasks:
            #     await asyncio.gather(*(task for task in self.__tasks))
            
            # await asyncio.sleep(self.__async_time)
     
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
        print(f"flag_session_set {flag}")
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
    
    @property
    def whoami(self):
        return self.__whoami
    
    @property
    def queue(self):
            return self.__queue
        
    @queue.setter
    def queue(self, queue):
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
    
    def update_timestamp_t2(self):
        self.__timestamp_t2.start()
        
    @classmethod
    def get_all_instances(cls):
        return cls.__instances
    
    @classmethod
    def get_instance(cls, id: int):
        for inst in cls.__instances:
            if inst.id == id:
                return inst
        return None
    
    ################################################
    ## RECEIVE FRAME
    async def handle_messages(self):
        while True:
            if self.__flag_delete:
                break
            
            # await asyncio.sleep(self.__async_time) # kritický bod pro rychlost ap 
            await asyncio.sleep(0.01) # kritický bod pro rychlost ap 
            try:
                print(f"Starting async handle_messages")
                
                # zde změřit zda timeout nedělá problém zbrždění
                # header = await asyncio.wait_for(self.__reader.read(2),timeout=0.2)
                header = await self.__reader.read(2)
                
                if header:
                    start_byte, frame_length = header
                    
                    # identifikace IEC 104
                    if start_byte == Frame._start_byte:
                        apdu = await self.__reader.read(frame_length)
                        if len(apdu) == frame_length:
                            new_apdu = Parser.parser(apdu,frame_length)
                            
                            
                            print(f"{time.ctime()} - Receive frame: {new_apdu}")
                            
                            
                            
                            # aktualizace poslední aktivity 
                            self.__timestamp_t0.start()
                            self.__timestamp_t1.start()
                            self.__timestamp_t2.start()
                            self.__timestamp_t3.start()
                            
                            await self.__incomming_queue.on_message_received((self, new_apdu))
                            self.__local_queue.put_nowait(new_apdu)
                            
                            # allow to event
                            self.__event_update.set()
                            
                            print(f"Finish async handle_messages.")
                            
                            # reset local vars
                            header = None
                            start_byte = None
                            apdu = None
                            new_apdu = None
                            frame_length = None
                            # return new_apdu
                else:
                    print(f"zadne prichozi zpravy")
                    
                            
                        
                # přijat nějaký neznámý formát
            except asyncio.TimeoutError:
                print(f'Klient {self} neposlal žádná data.')
                
            except Exception as e:
                print(f"Exception {e}")
        
    ################################################
    ## SEND FRAME
    async def send_frame(self,frame: Frame = None):
        while True:
            if self.__flag_delete:
                break
            
            try:
                # await asyncio.sleep(self.__async_time) # kritický bod pro rychlost ap    
                print(f"Start send_frame_task()")
                
                await self.__event_out.wait()
                self.__event_out.clear()
                
                # print("\x1b[31mToto je červený text.\x1b[0m")
                if frame is not None:
                    print(f"{time.ctime()} - Send frame: {frame}")
                    self.__writer.write(frame.serialize())                    
                    print("\x1b[31mToto již nikdy nevytiskne "
                          "páč tu funkci nevolám s parametrem.\x1b[0m")
                    await self.__writer.drain()
                    
                else:
                    if not self.__outgoing_queue.is_Empty():
                        print(f"posílá se neco z odchozí fronty")
                        session, frame = await self.__outgoing_queue.get_message()
                        
                        if session == self:
                            print(f"{time.ctime()} - Send frame: {frame}")
                            self.__writer.write(frame.serialize())
                            await self.__writer.drain()
                        
                        
                   
                # add to packet buffer
                if isinstance(frame, IFormat):
                    self.__send_buffer.add_frame(frame.ssn, frame)  
                          
            except asyncio.QueueEmpty:
                print(f"problem v asynciu")
            except Exception as e:
                print(f"Exception {e}")
            
            
            # reset local var 
            if frame:
                frame = None
                
                # update timer t1, after frame
                # self.__timestamp_t1.start()
                
            print(f"Stop send_frame_task()")
        
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
        
    @property
    def connection_info(self):
        return self.__ip, self.__port, self.__connection_state, self.__transmission_state, self._timeout
    
    async def check_for_timeouts(self):
        while True:
            if self.__flag_delete:
                break
            
            await asyncio.sleep(self.__time_for_task_timeouts) # kritický bod pro rychlost ap    
            print(f"Starting async check_for_timeouts")
            
            allow_event_signal = 0
            
            # TIMEOUT T0 
            if self.__timestamp_t0.timed_out:
                print(f"Timer t0 timed_out")
                allow_event_signal = 1
                print(f'Client {self.__ip}:{self.__port} timed out and disconnected')
                self.flag_session = 'ACTIVE_TERMINATION'
                
            # TIMEOUT T1    
            if self.__timestamp_t1.timed_out:
                print(f"Timer t1 timed_out")
                allow_event_signal = 1
                self.flag_timeout_t1 = 1
                print(f"Timeout t1 is set to 1")
                # raise TimeoutError(f"Timeout pro t1")
                
            # TIMEOUT T2     
            if self.__timestamp_t2.timed_out:
                print(f"Timer t2 timed_out")
                allow_event_signal = 1
                if not self.__recv_buffer.is_empty():
                    resp = await self.__queue.generate_s_frame(self)
                    await self.__outgoing_queue.to_send((self,resp))
                    
            # TIMEOUT T3     
            if self.__timestamp_t3.timed_out:
                print(f"Timer t3 timed_out")
                allow_event_signal = 1 
                frame = self.__queue.generate_testdt_act()
                await self.__outgoing_queue.to_send((self,frame))
            
            if allow_event_signal:
                # allow to event
                self.__event_update.set()  
                
                
            # self.loop.create_task()
            print(f"*******************************")
            # print(f"\t {str(time.time() - last_timestamp)[:5]}")
            print(f"*******************************")
            print(f"Finish async check_for_timeouts")
        
    
    async def update_state_machine_server(self, fr: Frame = None):
        while True:
            if self.__flag_delete:
                break
            
            # wait for allow
            await self.__event_update.wait()
            self.__event_update.clear()
            
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
                        fr = await self.__local_queue.get()
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
                                await self.__outgoing_queue.to_send((self,new_frame))
                            
                            # S-format or I-format   
                            if frame == 'S-format' or frame == 'I-format':
                                    self.flag_session = 'ACTIVE_TERMINATION'
                                    
                        
                        #* STATE 2 
                        if actual_transmission_state == 'RUNNING':
                            
                            # if frame is stopdt act and send queue is blank
                            if frame == acpi.STOPDT_ACT:
                                
                                if self.__recv_buffer.is_empty() and\
                                    self.__send_buffer.is_empty():
                                    
                                    new_frame = self.__queue.generate_stopdt_con()
                                    await self.__outgoing_queue.to_send((self,new_frame))
                                    # poslat STOPDT CON
                                    self.transmission_state = 'STOPPED'
                            
                            
                                else:# if frame is stopdt act and send queue is not blank
                                    if not self.__recv_buffer.is_empty(): 
                                        
                                        # ack all received_I-formats
                                        new_frame = await self.__queue.generate_s_frame(self)
                                        await self.__outgoing_queue.to_send((self,new_frame))
                                    
                                    self.transmission_state = 'WAITING_UNCONFIRMED'
                            
                        
                        #* STATE 3 
                        if actual_transmission_state == 'WAITING_UNCONFIRMED':
                            
                            if frame == 'S-format':
                                if self.__send_buffer.is_empty() and \
                                    self.__recv_buffer.is_empty():
                                           
                                    # poslat STOPDT CON
                                    new_frame = self.__queue.generate_stopdt_con()
                                    await self.__outgoing_queue.to_send((self,new_frame))
                                    
                                    # change state to 'STOPPED'
                                    self.transmission_state = 'STOPPED'

                                if not self.__recv_buffer.is_empty(): 
                                        # ack all received_I-formats
                                        new_frame = await self.__queue.generate_s_frame(self)
                                        await self.__outgoing_queue.to_send((self,new_frame))
                                
                            #  I-format   
                            if frame == 'I-format':
                                self.flag_session = 'ACTIVE_TERMINATION'
                    
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
                        # del self
                        # self.queue.del_session(self)
                        await self.delete_self()
                        
                        
                else:
                    pass
                    
                
                print(f"{self.connection_state}")
                print(f"{actual_transmission_state}")
                
                await asyncio.sleep(self.__async_time)
                print(f"Finish async update_state_machine_server")
                
            except Exception as e:
                print(f"Exception {e}")
            
            finally:
                pass
                
    async def update_state_machine_client(self, fr: Frame = None):
        while True:
            if self.__flag_delete:
                break
            
            # wait for allow
            await self.__event_update.wait()
            self.__event_update.clear()
            
            try:
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
                        fr = await self.__local_queue.get()
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
                                await self.__outgoing_queue.to_send((self,new_frame))
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
                            
                            # END RUNNING
                            if self.flag_session == 'STOP_SESSION':
                                                                
                                # reset flag for start session
                                self.flag_session = None
                                
                                # To WAITING_STOPPED
                                if self.__recv_buffer.is_empty() and \
                                    self.__send_buffer.is_empty():
                                                                        
                                    # send stopdt act
                                    new_frame = self.__queue.generate_stopdt_act()
                                    await self.__outgoing_queue.to_send((self,new_frame))
                                    # update state
                                    self.transmission_state = 'WAITING_STOPPED'
                            
                                else: 
                                    # To WAITING_UNCONFIRMED
                                    if not self.__recv_buffer.is_empty():
                                                                            
                                        # ack all received_I-formats
                                        new_frame = await self.__queue.generate_s_frame(self)
                                        await self.__outgoing_queue.to_send((self,new_frame))
                                        
                                    # send stopdt act
                                    new_frame = self.__queue.generate_stopdt_act()
                                    await self.__outgoing_queue.to_send((self,new_frame))
                                    # update state
                                    self.transmission_state = 'WAITING_UNCONFIRMED'
                                                        
                        
                        #* STATE 4 
                        if actual_transmission_state == 'WAITING_UNCONFIRMED':
                            
                            if frame == acpi.STOPDT_CON:
                                self.transmission_state = 'STOPPED'
                            
                            if  (frame == 'I-format' or frame == 'S-format' ) and \
                                (self.__send_buffer.is_empty() and \
                                     self.__recv_buffer.is_empty()):
                                         
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
                        # del self
                        await self.delete_self()
                        
                else:
                    pass
                    
                
                print(f"{self.connection_state}")
                print(f"{actual_transmission_state}")
                
                await asyncio.sleep(self.__async_time)
                print(f"Finish async update_state_machine_client")
                
            except Exception as e:
                print(f"Exception {e}")
        
        self.__task_state.resu
                
    async def delete_self(self):
        self.__flag_delete = True
        self.queue.del_session(self)

        await asyncio.gather(self.__task_handle_messages.cancel(),
                            self.__task_send_frame.cancel(),
                            self.__task_state.cancel(),
                            self.__task_timeouts.cancel(),
                            return_exceptions=True)
        del self
        
    
        
    def __enter__(self):
        pass
    def __str__(self):
        return (f"SessionID: {self.__id}, ip: {self.__ip}, port: {self.__port}, connected: {self.is_connected}")
       
        
    def __exit__(*exc_info):
        pass