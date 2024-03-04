# -*- coding: utf-8 -*-
# import readline
import os
import socket
import binascii
import sys
from Parser import Parser
from QueueManager import QueueManager
import acpi
import struct
import logging
from config_loader import ConfigLoader
import threading
import Frame
import time
import Session
from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
import asyncio
import time





LOG = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


class IEC104Client(object):
    def __init__(self, loop):
        print(os.getcwd())
        self.servers = [] # tuple (ip, port, queue)
        self.queue = QueueManager()
        self.data = 'vymyslena data'
        self.data = 0x65 + \
                    0x01 + \
                    0x0A + \
                    0x00 + \
                    0x0C + \
                    0x00 + \
                    0x00 + \
                    0x00 + \
                    0x00 + \
                    0x05
        
        self.loop = loop
        self.no_overflow = 0
        # self.loop = asyncio.get_event_loop()
        
                    
        self.data = struct.pack(f"{'B' * 10}", 
                                    0x65, # start byte
                                    0x01,  # Total Length pouze hlavička
                                    0x0A,   # 1. ridici pole
                                    0x00,  # 2. ridici pole
                                    0x0C,   # 3. ridici pole
                                    0x00,  # 4. ridici pole hlavička
                                    0x00,   # 1. ridici pole
                                    0x00,  # 2. ridici pole
                                    0x00,   # 3. ridici pole
                                    0x05,   # 3. ridici pole
        )
        config_loader = ConfigLoader('./v2.0/config_parameters.json')

        self.server_ip = config_loader.config['server']['ip_address']
        self.server_port = config_loader.config['server']['port']
        
        
        # load configuration parameters
        try:
            self.k, self.w, \
            self.timeout_t0, \
            self.timeout_t1, \
            self.timeout_t2, \
            self.timeout_t3 = self.load_params(config_loader)
            
            self.session_params = ( self.k,
                                   self.w,
                                   self.timeout_t0,
                                   self.timeout_t1,
                                   self.timeout_t2,
                                   self.timeout_t3 )
        
        except Exception as e:
            print(e)
    
    def load_params(self, config_loader):
        
        k = config_loader.config['server']['k']
        if k < 1 or k > 32767:
            raise Exception("Wrong value range for \'k\' variable!")
        
        w = config_loader.config['server']['w']
        if w > ((k*2)/3):  
            if w < 1 or w > 32767:
                raise Exception("Wrong value range for \'w\' variable!")
            print(f"Warning! Use value range for \'w\' less than 2/3 of \'k\'")
        
        t0 = config_loader.config['server']['t0']
        if t0 < 1 or t0 > 255:
            raise Exception("Wrong value range for \'t0\' variable!")
        
        t1 = config_loader.config['server']['t1']
        if t1 < 1 or t1 > 255:
            raise Exception("Wrong value range for \'t1\' variable!")
        
        t2 = config_loader.config['server']['t2']
        if t2 < 1 or t2 > 255:
            raise Exception("Wrong value range for \'t2\' variable!")
        
        t3 = config_loader.config['server']['t3']
        if t3 < 1 or t3 > 172800:
            raise Exception("Wrong value range for \'t3\' variable!")
        
        return k, w, t0, t1, t2, t3
    
    async def new_session(self, ip, port):
        try:
            self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout = self.timeout_t0
                    )
            
            client_address, client_port =self.writer.get_extra_info('sockname')
            print(f"Navázáno {client_address}:{client_port}-->{self.server_ip}:{self.server_port}")
            
            self.session = Session.Session( self.server_ip,
                                            self.server_port,
                                            self.reader,
                                            self.writer,
                                            self.session_params )
            
            self.queue.add_session((self.server_ip, self.server_port, self.session))
            self.active_session = self.queue.Select_active_session(self.session)
            return self.active_session
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(e)
        
    async def run_client(self):        
        try:
            print(f"Vytáčím {self.server_ip}:{self.server_port}")
            
            # přidá novou session a zároveň vybere aktivní session
            self.active_session = await self.new_session(self.server_ip,
                                                         self.server_port )
            
            # tuple (ip, port, queue)
            self.servers.append( (self.server_ip,   
                                 self.server_port,
                                 self.queue) )
            
            self.task = self.loop.create_task(self.periodic_event_check())
            await self.main()
            # async with asyncio.TaskGroup() as group:
            #     group.create_task(self.periodic_event_check())
                # group.create_task()
            
            
        except Exception as e:
            print(e) 
            
            
    async def nejaka_funkce(self):
        try: 
            frame1 = UFormat(acpi.STARTDT_ACT)
            self.writer.write(frame1.serialize())
            print(f"{time.ctime()} - Odeslán rámec: {frame1}")
            
            resp = await self.listen()
            
            if isinstance(resp, UFormat):
                
                print(f"{time.ctime()} - Přijat rámec: {resp}")
                frames1 = []
                frames2 = []
                for i in range(0,4):
                    frames1.append(UFormat(acpi.TESTFR_ACT))
                    self.writer.write(frames1[i].serialize())
                    await self.writer.drain()
                    print(f"Odeslán rámec: {frames1[i]}")
                    
                    resp = await self.listen()
                    if isinstance(resp, UFormat):
                        print(f"Ok, přijat Testdt con")
                        time.sleep(2)
                    else:
                        break
                    time.sleep(5)
                    
                for i in range(0,1):
                    frames2.append(IFormat(self.data, self.queue_man.get_VS(), self.queue_man.get_VR()))
                    self.queue.insert_send_queue(frames2[i])
                    self.writer.write(frames2[i].serialize())
                    
                    await self.writer.drain()
                    print(f"{time.ctime()} - Odeslán rámec: {frames2[i]}")
                    self.queue_man.incrementVS()
                    
                    resp = await self.listen()
                    if resp:
                        print(f"{time.ctime()} - Přijat rámec: {resp}")
                    if isinstance(resp, UFormat):
                        pass
                    if isinstance(resp, IFormat):
                        self.queue_man.insert_send_queue(resp)
                        self.queue_man.incrementVR()
                        self.queue_man.set_ack(resp.get_rsn())
                        self.queue_man.clear_acked_send_queue()
                    
                    if isinstance(resp, SFormat):
                        self.queue_man.set_ack(resp.get_rsn())
                        self.queue_man.clear_acked_send_queue()
                    else:
                        break
                    
                    time.sleep(5)
                    
            
            if isinstance(resp, IFormat):
                self.queue_man.insert_send_queue(resp)
                self.queue_man.incrementVR()
                self.queue_man.set_ack(resp.get_rsn())
                self.queue_man.clear_acked_send_queue()
            
            if isinstance(resp, SFormat):
                self.queue_man.set_ack(resp.get_rsn())
                self.queue_man.clear_acked_send_queue()
            
        except Exception as e:
            pass
    
    async def handle_messages(self):
        
        try:
            while True:
                print(f"Starting async handle_messages")
                
                header = await asyncio.wait_for(self.reader.read(2),timeout=2)
                
                if not header:
                    break
                
                start_byte, frame_length = header
                
                # identifikace IEC 104
                if start_byte == Frame.Frame.start_byte:
                    apdu = await self.reader.read(frame_length)
                    if len(apdu) == frame_length:
                        new_apdu = Parser.parser(apdu,frame_length)
                        
                        # aktualizace poslední aktivity 
                        self.active_session.update_timestamp()
                        
                        # if isinstance(new_apdu, UFormat):
                        #     self.loop.create_task(self.handle_U_format(new_apdu))
                        
                        print(f"Finish async handle_messages.")
                        await self.handle_response(new_apdu)
                        
        except asyncio.TimeoutError:
            print(f'Klient {self.ip} neposlal žádná data.')
        except asyncio.CancelledError:
            pass         
        except Exception as e:
            print(f"Exception {e}")
        
    async def handle_response(self,apdu):
        
        if isinstance(self.active_session, Session.Session):
            # STATE MACHINE
            if self.active_session.get_connection_state() == 'Connected':
                
                # STATE 1
                if self.active_session.get_transmission_state() == 'Stopped':
                    # send 2x testdt frame 
                    # send start act
                    pass
                
                # STATE 2
                if self.active_session.get_transmission_state() == 'Waiting_running':
                    # check if response is start con
                    # else send testdt frame 
                    pass
                
                # STATE 3
                if self.active_session.get_transmission_state() == 'Running':
                    # for cyklus for send I frame with random data
                    # check if response is ack with S format
                    # send testdt frame 
                    pass
                
                # STATE 4
                if self.active_session.get_transmission_state() == 'Waiting_unconfirmed':
                    # do not send new I frame, but check if response are I,S or U formats
                    # send testdt frame 
                    # check if response is stopdt con
                    pass
                
                # STATE 5
                if self.active_session.get_transmission_state() == 'Waiting_stopped':
                    # # do not send new I frame, but check if response are I,S or U formats
                    # send testdt frame 
                    # check if response is stopdt con
                    pass
                
                self.update_state_machne()
                
            else:
                
                pass
    
    async def update_state_machine(self, fr = 0):
        print(f"Starting async update_state_machine")
        
        # get_connection_state()
            # 0 = Disconnected
            # 1 = Connected
        if self.active_session.get_connection_state('Connected'):
            
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
            if self.active_session.get_transmission_state() == 'Stopped':
                
                # flag for start session is set
                if self.active_session.get_flag_session() == 'start_session':
                    
                    # reset flag for start session
                    self.active_session.set_flag_session(None)
                    # send start act
                    await self.active_session.response_startdt_act()
                    # update state
                    self.active_session.set_transmission_state('Waiting_running')
                
                
                # t1_timeout or S-format or I-format   
                if frame == 'S-format' or frame == 'I-format' or \
                    self.active_session.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.active_session.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.active_session.set_flag_session('active_termination')
                
            
            #* STATE 2 - 
            if self.active_session.get_transmission_state() == 'Waiting_running':
                
                if frame == acpi.STARTDT_CON:
                    self.active_session.set_transmission_state('Running')
                    pass
                
                # t1_timeout or S-format or I-format   
                if frame == 'S-format' or frame == 'I-format' or \
                    self.active_session.get_flag_timeout_t1():
                        
                        # reset flag for t1_timeout
                        self.active_session.set_flag_timeout_t1(0)
                        # aktivni ukonceni
                        self.active_session.set_flag_session('active_termination')
                        
                
            #* STATE 3 - 
            if self.active_session.get_transmission_state() == 'Running':
                
                # To pending_stopped
                if self.active_session.get_flag_session() == 'stop_session' and \
                    self.queue.isBlank_send_queue():
                        
                        # reset flag for start session
                        self.active_session.set_flag_session(None)
                        # send start act
                        await self.active_session.response_stopdt_act()
                        # update state
                        self.active_session.set_transmission_state('Waiting_stopped')
                
                # To pending_unconfirmed
                if self.active_session.get_flag_session() == 'stop_session' and \
                    not self.queue.isBlank_send_queue():
                        
                        # reset flag for start session
                        self.active_session.set_flag_session(None)
                        # send start act
                        await self.active_session.response_stopdt_act()
                        # update state
                        self.active_session.set_transmission_state('Waiting_unconfirmed')
                
                # t1_timeout    
                if self.active_session.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.active_session.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.active_session.set_flag_session('active_termination')
                    
            
            #* STATE 4 
            if self.active_session.get_transmission_state() == 'Waiting_unconfirmed':
                
                if frame == acpi.STOPDT_CON:
                    self.active_session.set_transmission_state('Stopped')
                
                if  (frame == 'I-format' or frame == 'S-format' ) and \
                    self.queue.isBlank_send_queue():
                        self.active_session.set_transmission_state('Waiting_stopped')
                  
                # t1_timeout    
                if self.active_session.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.active_session.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.active_session.set_flag_session('active_termination')
                    
                    
            #* STATE 5 
            if self.active_session.get_transmission_state() == 'Waiting_stopped':
                
                if frame == acpi.STOPDT_CON:
                    self.active_session.set_transmission_state('Stopped')
                
                # t1_timeout    
                if self.active_session.get_flag_timeout_t1():
                    
                    # reset flag for t1_timeout
                    self.active_session.set_flag_timeout_t1(0)
                    # aktivni ukonceni
                    self.active_session.set_flag_session('active_termination')
                 
                    
            # default condition if active_termination is set
            if self.active_session.get_flag_session() == 'active_termination':
                
                # unset active_termination 
                self.active_session.set_flag_session(None)
                self.active_session.set_transmission_state('Stopped')
                self.active_session.set_connection_state('Disconnected')
                   
        else:
            self.active_session.set_transmission_state('Stopped')
            self.active_session.set_connection_state('Disconnected')
            pass
        
        print(f"Finish async update_state_machine")

    async def check_for_message(self):
        if self.active_session.get_connection_state == 'Connected':
                self.loop.create_task(self.handle_messages())
    
        
    async def get_user_input(self, prompt):
        """
        Získá vstup od uživatele.
        """
        # readline.set_completer(None)
        # readline.set_completion_display_matches(False)
        return await asyncio.get_event_loop().run_in_executor(None, input, prompt)
    
   
    async def main(self):
        """
        Hlavní funkce UI.
        """
        if isinstance(self.active_session, Session.Session):
            
            while True:
                # Získá vstup od uživatele
                user_input = await self.get_user_input("I\nS\nU\n\
                    Vyberte formát rámce, který chcete poslet na server: ")

                # Zpracujte vstup
                if user_input == "quit":
                    break
                elif user_input == "help":
                    print("Dostupné příkazy: quit, help")
                    
                elif user_input == "I" or user_input == "i":
                    i_format_data = u_format = await self.get_user_input(f"zadejte data:")
                    frame = await self.queue.generate_i_frame(i_format_data)
                    # napsat natvrdo nějaké funkce z ASDU
                    await self.active_session.send_frame(frame)
                
                elif user_input == "S" or user_input == "s":
                    frame = await self.queue.generate_s_frame()
                    await self.active_session.send_frame(frame)
                    pass
                
                elif user_input == "U" or user_input == "u":
                    u_format = await self.get_user_input(f"start_act\n\
                        start_con\n\
                        stop_act\n\
                        stop_con\n\
                        testdt_act\n\
                        testdt_con\n\
                        ")
                    if u_format == "start_act":
                        await self.active_session.response_startdt_act()
                        pass
                    
                    if u_format == "start_con":
                        await self.active_session.response_startdt_con()
                        pass
                    
                    if u_format == "stop_act":
                        await self.active_session.response_stopdt_act()
                        pass
                    
                    if u_format == "stop_con":
                        await self.active_session.response_stopdt_con()
                        pass
                    
                    if u_format == "testdt_act":
                        await self.active_session.response_testdt_act()
                        pass
                    
                    if u_format == "testdt_con":
                        await self.active_session.response_testdt_con()
                        pass
                    
                    if u_format == "quit":
                        pass
                else:
                    print(f"Neznámý příkaz: {user_input}")
                
                await self.task
            
    async def listen(self):
        while True:
            try:
                header = await self.reader.read(2)
                
                if not header:
                    break
                # timeout a return
                
                start_byte, frame_length = header
                
                if start_byte == Frame.Frame.start_byte:
                    apdu = await self.reader.read(frame_length)
                    if len(apdu) == frame_length:
                        new_apdu = Parser.parser(apdu,frame_length)
                        
                        
                        
                        if isinstance(new_apdu, IFormat):
                            self.queue_man.insert_send_queue(new_apdu)
                            self.queue_man.incrementVR()
                            self.queue_man.set_ack(new_apdu.get_rsn())
                            self.queue_man.clear_acked_send_queue()
                            
                        if isinstance(new_apdu, SFormat):
                            self.queue_man.set_ack(new_apdu.get_rsn())
                            self.queue_man.clear_acked_send_queue()
                        
                        if isinstance(new_apdu, UFormat):
                            response = self.queue_man.Uformat_response(new_apdu)
                            if response:
                                self.writer.write(response.serialize())
                                await self.writer.drain()
                                return response
                                    
                            
                        return new_apdu
                    else:
                        raise Exception("Nastala chyba v přenosu, \
                                        přijatá data se nerovnájí požadovaným.")
                    
                else:
                    # zde pak psát logy
                    raise Exception("Přijat neznámý formát")
                
            except Exception as e:
                print(f"Exception {e}")
                sys.exit(1)
                
    
    async def periodic_event_check(self):
        print(f"Starting async periodic event check.")
        while True:
            
            
            for client in self.clients:
                # client is tuple (ip, queue)
                for session in client[1].get_sessions():
                    
                    # timeouts check 
                    self.loop.create_task(session.check_for_timeouts())
                    
                    # check client message
                    self.loop.create_task(self.check_for_message())
                
                # queue check
                # self.loop.create_task(self.queue.check_for_queue())
            
            # UI se nebude volat tak často jako ostatní metody
            self.no_overflow = self.no_overflow + 1
            if self.no_overflow > 2:
                    self.no_overflow = 0
                    
                    # musí se UI volat periodicky? 
                    # self.loop.create_task(self.main())
            
            # new client connected
                # is check automaticaly by serve.forever() 
            
            await asyncio.sleep(1)       

if __name__ == "__main__":
    
    loop = asyncio.new_event_loop()
    client = IEC104Client(loop)
    try:
        asyncio.run(client.run_client())
    except KeyboardInterrupt:
        pass
    finally:
        pass