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
    def __init__(self, loop=0): 
        self.config_loader = ConfigLoader('./v2.0/config_parameters.json')

        self.ip = self.config_loader.config['server']['ip_address']
        self.port = self.config_loader.config['server']['port']
        self.active_session = None
        self.queue = None
        self.clients = []   # tuple (ip, queue)
        
        self.loop = loop
        self.server = None
        self.lock = asyncio.Lock()
        
        
        # load configuration parameters
        try:
            self.k, self.w, \
            self.timeout_t0, \
            self.timeout_t1, \
            self.timeout_t2, \
            self.timeout_t3 = self.load_params(self.config_loader)
            
            self.session_params = (self.k, self.w, self.timeout_t0, self.timeout_t1, self.timeout_t2, self.timeout_t3)
        
        except Exception as e:
            print(e)
    
    async def set_loop(self, loop):
        self.loop = loop
        
    def load_params(self, config_loader):
        
        k = self.config_loader.config['server']['k']
        if k < 1 or k > 32767:
            raise Exception("Wrong value range for \'k\' variable!")
        
        w = self.config_loader.config['server']['w']
        if w > ((k*2)/3):  
            if w < 1 or w > 32767:
                raise Exception("Wrong value range for \'w\' variable!")
            print(f"Warning! Use value range for \'w\' less than 2/3 of \'k\'")
        
        t0 = self.config_loader.config['server']['t0']
        if t0 < 1 or t0 > 255:
            raise Exception("Wrong value range for \'t0\' variable!")
        
        t1 = self.config_loader.config['server']['t1']
        if t1 < 1 or t1 > 255:
            raise Exception("Wrong value range for \'t1\' variable!")
        
        t2 = self.config_loader.config['server']['t2']
        if t2 < 1 or t2 > 255:
            raise Exception("Wrong value range for \'t2\' variable!")
        
        t3 = self.config_loader.config['server']['t3']
        if t3 < 1 or t3 > 172800:
            raise Exception("Wrong value range for \'t3\' variable!")
        
        return k, w, t0, t1, t2, t3

   
    
    
    def isResponse(self):
        pass
    
    # pokud už nějaké spojení s daným klientem existuje, jen přidá toto spojení k frontě
    # jinak vytvoří novou frontu a přidá tam toto spojení
    # client = tuple (ip, port, queue)
    def add_new_client_session(self, client):
        ip = client[0] 
        port = client[1]
        session = client[2]
        
        # dosud žádný klient
        if  not self.clients:
            new_queue = QueueManager()
            new_queue.add_session(client)
            self.clients.append((ip, new_queue))
            session.add_queue(new_queue)
            return new_queue    # returt this queue
        
        # existující klienti, přiřadí danému klientovi další spojení
        for item in self.clients:
            if item[0] == ip:
                item[1].add_session((ip, port, session))
                session.add_queue(item[1])
                return item[1]  # returt this queue
            
            # nový klient, přiřadí mu spojení
            else:
                new_queue = QueueManager()
                new_queue.add_session(client)
                self.clients.append((ip, new_queue))
                session.add_queue(new_queue)
                return new_queue    # returt this queue
        
    # Main function
    async def start(self):
        loop = asyncio.get_event_loop_policy().get_event_loop()
        self.set_loop(loop)

        
        periodic_task = await self.loop.create_task(self.periodic_event_check)
        
        await server.serve_forever(self.handle_client, self.ip, self.port)

        #     async with asyncio.TaskGroup() as group:
        #         group.create_task(self.server.serve_forever())
        #         group.create_task(self.periodic_event_check())
            # await asyncio.gather(
            #     self.periodic_event_check(),
            #     print(f"Start serveru. - Naslouchám na {self.ip}:{self.port}"),                
            #     self.loop.create_task(self.server.serve_forever()),
                
                # log start server
            # )


    async def handle_client(self, reader, writer):
        
        # Ziskani info ze soketu,
        # pokud je to nove spojeni s danym klientem vytvori se pro nej nova fronta
        # pokud uz s danym klientem (podle ip add) jiz nejake spojeni existuje
        # priradi ho do stejne fronty 
        # urci se aktivni spojeni pro prenos uziv. dat
        client_address, client_port = writer.get_extra_info('peername')
        
        with self.lock:
            session = Session( client_address,
                              client_port,
                              reader,
                              writer,
                              self.session_params )
            self.queue = self.add_new_client_session((client_address, client_port, session))
            self.active_session = self.queue.Select_active_session(session)
            print(f"Spojení navázáno: s {client_address, client_port}, (Celkem spojení: {self.queue.get_number_of_connected_sessions()}))")
            
            await self.active_session.handle_messages()
        

    
    
    
    async def periodic_event_check(self):
        print(f"Starting async periodic event check.")
        while True:
            
            # update timers in all sessions instances
            for client in self.clients:
                # client is tuple (ip, queue)
                for session in client[1].get_sessions():
                    
                    # timeouts check 
                    await session.check_for_timeouts()
                    
                    # client message
                    await session.check_for_message()
                
                # queue check
                await client[1].check_for_queue()
            
            
            # new client connected
                # is check automaticaly by serve.forever()
            
            await asyncio.sleep(0.5)
            
            
            
        
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
