# Import required modules
import socket
import sys
import time
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
        
        
    def update_state_machine(self, time_stamp,frame):
        
        if not time_stamp.time_out():
        
        # set_connection_state()
            # 0 = Disconnected
            # 1 = Connected
            
        # get_connection_state()
            # 0 = Stopped
            # 1= Pending_running
            # 2 = Running
            # 3 = Pending_unconfirmed
            # 4 = Pending_stopped
            
            # STATE 1
            if not self.active_session.get_connection_state() and \
                self.active_session.get_transmission_state() and \
                frame == acpi.STARTDT_ACT:
                    
                self.active_session.set_transmission_state(2)
            #
            if not self.active_session.get_connection_state() and \
                self.active_session.get_transmission_state() and \
                frame == acpi.STARTDT_ACT:
                self.active_session.set_transmission_state(2)
            
            # STATE 2
            if not self.active_session.get_connection_state() and \
                self.active_session.get_transmission_state(2) and \
                frame == acpi.STARTDT_ACT:
                self.active_session.set_transmission_state(2)
            
        else:
            self.active_session.set_transmission_state(0)
            self.active_session.set_connection_state(1)
            # connection close       
        
    
    def receive_data(self, apdu):
        pass
    
    def send_data(self, apdu):
        pass
    
    def generate_resp(self, apdu):
        pass
    
    def keepalive(self):
        pass
    
    def isResponse(self):
        pass
    
    # pokud už nějaké spojení s daným klientem existuje, jen přidá toto spojení k frontě
    # jinak vytvoří novou frontu a přidá tam toto spojení
    # client = tuple (ip, port, queue)
    def add_new_client_session(self, client):
        if  not self.server_clients:
            new_queue = QueueManager()
            new_queue.add_session(client)
            self.server_clients.append((client[0], new_queue))
            return new_queue    # returt this queue
        for item in self.server_clients:
            if item[0] == client[0]:
                item[1].add_session(client)
                return item[1]  # returt this queue
            else:
                new_queue = QueueManager()
                new_queue.add_session(client)
                self.server_clients.append((client[0], new_queue))
                return new_queue    # returt this queue
        

    def Select_Session(self, session):
        # logika výběru aktivního spojení
        # zatím ponechám jedno a to to poslední
        return session
    
    # Main function
    async def start(self, loop = 0):
        
        self.server = await asyncio.start_server(
            self.server_handle_client, self.ip, self.port
            )
        async with self.server:
            print(f"Naslouchám na {self.ip}:{self.port}")
            await self.server.serve_forever()


    async def server_handle_client(self, reader, writer):
        # t0 = Timeout(acpi.T0)   # t0 = 30s
        # t1 = Timeout(acpi.T1)   # t1 = 15s
        # t2 = Timeout(acpi.T2)   # t2 = 10s
        # t3 = Timeout(acpi.T3)   # t3 = 20s
        
        
        
        
        client_address, client_port = writer.get_extra_info('peername')
        session = Session(client_address,client_port)
        self.queue = self.add_new_client_session((client_address, client_port, session))
        self.active_session = self.Select_Session(session)
        print(f"Spojení navázáno: s {client_address, client_port}, (Celkem spojení: {self.queue.get_number_of_established_sessions()}))")
        
        while True:
            try:
                
                
                
                # zkouším timeouty
                with Timeout(acpi.T0) as t0:
                    if t0.timed_out:
                        print(f"Timeout t0")
                with Timeout(acpi.T1) as t1:
                    if t1.timed_out:
                        print(f"Timeout t1")  
                with Timeout(acpi.T2) as t2:
                    if t2.timed_out:
                        print(f"Timeout t2")
                with Timeout(acpi.T3) as t3:
                    if t3.timed_out:
                        print(f"Timeout t3")
                # return_code = 
                #   0 - IFormat
                #   1 - SFormat 
                #   2-3 - UFormat - startdt seq
                #   4-5 - UFormat - stopdt seq
                #   6-7 - UFormat - testdt seq
                #   8   - Nic
                #   >=9 - Chyba
                
                # příjem   
                return_code, apdu = await self.active_session.handle_messages(reader, writer)
                
                if not t1.timed_out:
                    
                    if self.active_session.get_connection_state
                
                if return_code < 8:
                    if isinstance(apdu, IFormat):
                        self.queue.insert_send_queue(apdu)
                        self.queue.incrementVR()
                        self.queue.set_ack(apdu.get_rsn())
                        self.queue.clear_acked_send_queue()
                        
                        # prozatím tady napíšu potvrzování
                        response = SFormat(self.queue.get_VR())
                        if response:
                            writer.write(response.serialize())
                            await writer.drain()
                            print(f"{time.ctime()} - Odeslána odpověď: {response}")
                        
                    if isinstance(apdu, SFormat):
                        self.queue.set_ack(apdu.get_rsn())
                        self.queue.clear_acked_send_queue()
                    
                    if isinstance(apdu, UFormat):
                        response = self.queue.Uformat_response(apdu)
                        if response:
                            writer.write(response.serialize())
                            await writer.drain()
                            print(f"{time.ctime()} - Odeslána odpověď: {response}")
                        
                    
                    
                    
                    # zde se mohou provádět akce s přijatými daty
                    
                    #return new_apdu
                else:
                    raise Exception(f"Chyba - nejspíš v implementaci, neznámý formát")
                
                #vysílat
                self.isResponse()
                      
            except Exception as e:
                
                print(f"Exception {e}")
                if e.find('WinError'):
                    print(f"Zachycen str \'WinError\' ")
                    sys.exit(1)
        
            
        
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
