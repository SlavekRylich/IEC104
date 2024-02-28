# Import required modules
import socket
import sys
import time
import traceback
from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
from Parser import Parser
import acpi
from config_loader import ConfigLoader
import asyncio
from Session import Session
import Frame
from QueueManager import QueueManager
from Timeout import Timeout
from State import StateConn,StateTrans


LISTENER_LIMIT = 5

class ServerIEC104():
    
    # constructor for IEC104 server
    def __init__(self,loop=0): 
        config_loader = ConfigLoader('config_parameters.json')

        self.ip = config_loader.config['server']['ip_address']
        self.port = config_loader.config['server']['port']
        self.active_session = None
        self.queue = None
        self.last_time = 0
        # tuple (ip, queue)
        self.server_clients = []
        
        
        self.k = config_loader.config['server']['k']
        if self.k < 1 or self.k > 32767:
            raise Exception("Wrong value range for \'k\' variable!")
        
        self.w = config_loader.config['server']['w']
        if self.w > ((self.k*2)/3):  
            if self.w < 1 or self.w > 32767:
                raise Exception("Wrong value range for \'w\' variable!")
            print(f"Warning! Use value range for \'w\' less than 2/3 of \'k\'")
        
        self.t0 = config_loader.config['server']['t0']
        if self.t0 < 1 or self.t0 > 255:
            raise Exception("Wrong value range for \'t0\' variable!")
        
        self.t1 = config_loader.config['server']['t1']
        if self.t1 < 1 or self.t1 > 255:
            raise Exception("Wrong value range for \'t1\' variable!")
        
        self.t2 = config_loader.config['server']['t2']
        if self.t2 < 1 or self.t2 > 255:
            raise Exception("Wrong value range for \'t2\' variable!")
        
        self.t3 = config_loader.config['server']['t3']
        if self.t3 < 1 or self.t3 > 172800:
            raise Exception("Wrong value range for \'t3\' variable!")
        
        
    def update_state_machine(self, t1,fr = 0):
        
            # set_connection_state()
                # 0 = Disconnected
                # 1 = Connected
            if  self.active_session.get_connection_state('Connected'):
                
                if not t1.time_out:
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
                        frame = fr.get_type_in_word()
                    
                    # STATE 1   - if stopped and U-frame(STARTDT ACT)
                    if self.active_session.get_transmission_state() == 'Stopped' and \
                        frame == acpi.STARTDT_ACT:
                        
                        # poslat STARTDT CON
                        self.active_session.set_transmission_state('Running')
                        self.active_session.response_startdt_con()
                        t1.start()
                        
                    # #   - if stopped and U-frame(other)
                    # if  self.active_session.get_transmission_state() and \
                    #     frame != acpi.STARTDT_ACT:
                            
                    #     self.active_session.set_transmission_state(2)
                    
                    # STATE 2   - if running and U-frame(STOPDT ACT) and send_queue is blank
                    if self.active_session.get_transmission_state() == 'Running' and \
                        frame == acpi.STOPDT_ACT and \
                         not self.queue.isBlank_send_queue():
                             
                             # poslat STOPDT CON
                            self.active_session.set_transmission_state('Stopped')
                            self.active_session.response_stopdt_con()
                            t1.start()
                            
                            
                    # STATE 2   - if running and U-frame(STOPDT ACT) and send_queue is not blank
                    if self.active_session.get_transmission_state() == 'Running' and \
                        frame == acpi.STOPDT_ACT and \
                         self.queue.isBlank_send_queue():
                             
                             # poslat STOPDT CON
                            self.active_session.set_transmission_state('Pending_unconfirmed')
                            t1.start()
                    
                    
                    # STATE 3   - if Pending_unconfirmed and S-Frame and send_queue is blank
                    if self.active_session.get_transmission_state() == 'Pending_unconfirmed' and \
                        frame.get_type_in_word() == 'S-format' and \
                         not self.queue.isBlank_send_queue():
                             
                             # poslat STOPDT CON
                            self.active_session.set_transmission_state('Stopped')
                            self.active_session.response_stopdt_con()
                            t1.start()
                    
                else:
                    self.active_session.set_transmission_state('Stopped')
                    self.active_session.set_connection_state('Disconnected')
                    raise Exception(f"Timeout pro t1")
                    # connection close       

            else:
                self.active_session.set_transmission_state('Stopped')
                self.active_session.set_connection_state('Disconnected')
                pass
    
   
    
    
    def isResponse(self):
        pass
    
    # pokud už nějaké spojení s daným klientem existuje, jen přidá toto spojení k frontě
    # jinak vytvoří novou frontu a přidá tam toto spojení
    # client = tuple (ip, port, queue)
    def add_new_client_session(self, client):
        ip = client[0] 
        port = client[1]
        session = client[2]
        
        if  not self.server_clients:
            new_queue = QueueManager()
            new_queue.add_session(client)
            self.server_clients.append((ip, new_queue))
            return new_queue    # returt this queue
        
        for item in self.server_clients:
            if item[0] == ip:
                item[1].add_session((ip, port, session))
                return item[1]  # returt this queue
            else:
                new_queue = QueueManager()
                new_queue.add_session(client)
                self.server_clients.append((ip, new_queue))
                return new_queue    # returt this queue
        

    def Select_Session(self, session):
        # logika výběru aktivního spojení
        # zatím ponechám jedno a to to poslední
        for item in self.queue.get_connected_sessions():
            if item.get_connection_state() == 'Connected':
                pass
        return session
    
    # Main function
    async def start(self):
        
        self.server = await asyncio.start_server(
            self.server_handle_client, self.ip, self.port
            )
        async with self.server:
            print(f"Naslouchám na {self.ip}:{self.port}")
            await self.server.serve_forever()


    async def server_handle_client(self, reader, writer):
        # jen zde definuji
        t0 = Timeout(self.t0)   # t0 = 30s
        t1 = Timeout(self.t1)   # t1 = 15s
        t2 = Timeout(self.t2)   # t2 = 10s
        t3 = Timeout(self.t3)   # t3 = 20s
        
        
        
        # Ziskani info ze soketu,
        # pokud je to nove spojeni s danym klientem vytvori se pro nej nova fronta
        # pokud uz s danym klientem (podle ip add) jiz nejake spojeni existuje
        # priradi ho do stejne fronty 
        # urci se aktivni spojeni pro prenos uziv. dat
        client_address, client_port = writer.get_extra_info('peername')
        session = Session(client_address,client_port)
        self.queue = self.add_new_client_session((client_address, client_port, session))
        self.active_session = self.Select_Session(session)
        print(f"Spojení navázáno: s {client_address, client_port}, (Celkem spojení: {self.queue.get_number_of_connected_sessions()}))")
        
        while True:
            try:
                # # zkouším timeouty
                # with Timeout(acpi.T0) as t0:
                #     if t0.timed_out:
                #         print(f"Timeout t0")
                # with Timeout(acpi.T1) as t1:
                #     if t1.timed_out:
                #         print(f"Timeout t1")  
                # with Timeout(acpi.T2) as t2:
                #     if t2.timed_out:
                #         print(f"Timeout t2")
                # with Timeout(acpi.T3) as t3:
                #     if t3.timed_out:
                #         print(f"Timeout t3")
                
                if t0.timed_out:
                    pass
                
                if t1.timed_out:
                    self.active_session.set_transmission_state('Stopped')
                    self.active_session.set_connection_state('Disconnected')
                    raise Exception(f"Timeout pro t1")
                    # connection close
                
                if t2.timed_out:
                    resp = self.queue.response_S_format()
                    self.active_session.send_frame(resp)
                
                if t3.timed_out:
                    self.active_session.response_testdt_act()
                
                
                apdu = await asyncio.wait_for(self.active_session.handle_messages(reader, writer),timeout=2)
                print(f"{time.ctime()} - Přijat rámec: {apdu}")
                # STATE MACHINE
                if self.active_session.get_transmission_state() == 'Stopped':
                    
                    
                    if isinstance(apdu, UFormat):
                        
                        if apdu.get_type_int() != acpi.STARTDT_ACT:
                            
                            if apdu.get_type_int() == acpi.TESTFR_ACT:
                                self.active_session.response_testdt_con()
                            
                            if apdu.get_type_int() == acpi.TESTFR_CON:
                                t3.start()
                                        
                    self.update_state_machine(t1, apdu) 
                    
                
                if self.active_session.get_transmission_state() == 'Running':
                    
                    if isinstance(apdu, IFormat):
                        # aktualizovat timer
                        self.queue.insert_send_queue(apdu)
                        self.queue.incrementVR()
                        self.queue.set_ack(apdu.get_rsn())
                        self.queue.clear_acked_send_queue()
                        t2.start()
                        
                    if isinstance(apdu, SFormat):
                        self.queue.set_ack(apdu.get_rsn())
                        self.queue.clear_acked_send_queue()
                        t3.start()
                    
                    if isinstance(apdu, UFormat):
                        if apdu.get_type_int() != acpi.STOPDT_ACT:
                            
                            if apdu.get_type_int() == acpi.TESTFR_ACT:
                                self.active_session.response_testdt_con()
                                t3.start()
                            
                            if apdu.get_type_int() == acpi.TESTFR_CON:
                                t3.start()
                                
                    
                    self.update_state_machine(t1, apdu)
                    
                    #vysílat vygenerovanou odpoved v odesilaci frontě -> implementovat do Session
                    if self.isResponse():
                        for item in self.queue.get_recv_queue():
                            writer.write(item.serialize())
                            await writer.drain()
                            
                        t0.start()   # t0 = 30s
                        t1.start()   # t1 = 15s
                        t2.start()   # t2 = 10s
                        t3.start()   # t3 = 20s
                
                
                
                if self.active_session.get_transmission_state() == 'Pending_unconfirmed':
                    
                    if isinstance(apdu, SFormat):
                        self.queue.set_ack(apdu.get_rsn())
                        self.queue.clear_acked_send_queue()
                        t3.start()
                    
                    if isinstance(apdu, UFormat):
                        
                        if apdu.get_type_int() != acpi.STOPDT_ACT:
                            
                            if apdu.get_type_int() == acpi.TESTFR_ACT:
                                self.active_session.response_testdt_con()
                                t3.start()
                            
                            if apdu.get_type_int() == acpi.TESTFR_CON:
                                t3.start()
                                        
                    self.update_state_machine(t1, apdu)
            
            except asyncio.TimeoutError:
                continue       
                      
            except Exception as e:
                traceback.print_exc()
                print(f"Exception {e}")
                self.close()
                # if e.find('WinError'):
                #     print(f"Zachycen str \'WinError\' ")
                #     sys.exit(1)
        
            
        
    async def close(self):
        self.loop.close()

        
if __name__ == '__main__':
    
    server = ServerIEC104()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        pass
    finally:
        pass
