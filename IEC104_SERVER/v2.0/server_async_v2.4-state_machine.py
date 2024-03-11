# Import required modules
import sys
import time
import asyncio

from IFormat import IFormat
from SFormat import SFormat
from UFormat import UFormat
from Parser import Parser
from config_loader import ConfigLoader
from Session import Session
from QueueManager import QueueManager 
from Timeout import Timeout
from State import StateConn,StateTrans
from IncomingQueueManager import IncomingQueueManager
from OutgoingQueueManager import OutgoingQueueManager


LISTENER_LIMIT = 5

class ServerIEC104():
    """
    Class for server IEC 104 protocol.
    """
    def __init__(self): 
        """
        Constructor for server IEC 104 protocol.
        Args: None
        Returns: None
        Exceptions: None
        """
        self.config_loader = ConfigLoader('./v2.0/config_parameters.json')

        self.ip = self.config_loader.config['server']['ip_address']
        self.port = self.config_loader.config['server']['port']
        
        self.queues = []  
        self.clients: dict[QueueManager] = {}
        
        self.lock = asyncio.Lock()
        self.no_overflow = 0
        # self._loop = asyncio.get_event_loop_policy().get_event_loop()

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
    
        
        self._incoming_queue = IncomingQueueManager()
        self._outgoing_queue = OutgoingQueueManager()
    
        """Returned value:
        """
    @property
    def event_loop(self):
        return self._loop
    
    @event_loop.setter
    def event_loop(self, loop):
        self._loop = loop
        
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

   
    
    
    def isResponse(self):
        pass
    
    # pokud už nějaké spojení s daným klientem existuje, jen přidá toto spojení k frontě
    # jinak vytvoří novou frontu a přidá tam toto spojení
    # client = tuple (ip, port, queue)
    def add_new_session(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        
        client_address, client_port = writer.get_extra_info('peername')
        
        session = Session( client_address,
                            client_port,
                            reader,
                            writer,
                            self.session_params )
        
        # no client in queues yet
        if  not self.queues:
            new_queue = QueueManager(client_address)
            new_queue.add_session(session)
            self.queues.append(new_queue)
            session.add_queue(new_queue)
            return session,new_queue    # returt this queue
        
        else:
            # existující klienti, přiřadí danému klientovi další spojení
            for queue in self.queues:
                if queue.get_ip() == client_address:
                    queue.add_session(session)
                    session.add_queue(queue)
                    return session,queue  # returt this queue
                
            # nový klient, přiřadí mu spojení
            new_queue = QueueManager()
            new_queue.add_session(session)
            self.queues.append(new_queue)
            session.add_queue(new_queue)
            return session,new_queue    # returt this queue
        
    async def listen(self):
        print(f"Naslouchám na {self.ip}:{self.port}")
        self._server = await asyncio.start_server(self.handle_client,
                                            self.ip,
                                            self.port)
        
        
    async def start(self):
        # periodic_task = self._loop.create_task(self.periodic_event_check())
        # periodic_task = loop.run_forever(self.periodic_event_check)
        
        self._server = await asyncio.start_server(
            self.handle_client, self.ip, self.port
            )
        
        print(f"Naslouchám na {self.ip}:{self.port}")
        await asyncio.gather(self._server.serve_forever())
        
        #     async with asyncio.TaskGroup() as group:
        #         group.create_task(self.server.serve_forever())
        #         group.create_task(self.periodic_event_check())
                
                # log start server
            # )

    """
    Handle client.
    Args: reader, writer
    """
    async def handle_client(self, reader, writer):
        
        
        client_address, client_port = writer.get_extra_info('peername')
        
        """
        Create queue if not exist for that client.
        """
        if client_address not in self.clients:
            self.clients[client_address] = QueueManager(client_address)
            
        session = Session(client_address,
                            client_port,
                            reader,
                            writer,
                            self.session_params,
                            self.clients[client_address],
                            self.clients[client_address].in_queue,
                            self.clients[client_address].out_queue,
                            self.clients[client_address].packet_buffer)
        
        print(f"Spojení navázáno: s {client_address, client_port},\
                    (Celkem spojení: \
                        {self.clients[client_address].get_number_of_connected_sessions()}))")
        session.start()  

        
        # request = await self.active_session.handle_messages()
        # if request:
        #     await self.queue.handle_apdu(request)
            
            
    
    async def run(self):
        # await self._server
        # await asyncio.gather(*[session.run() for session in self.clients.values()])
        await asyncio.gather(self._server.serve_forever(),*[queue.run() for queue in self.clients.values()])
    
    # tady sem skoncil
    def check_alive_clients(self):
        for queue in self.queues:
            if isinstance(queue, QueueManager):
                if not queue.check_alive_sessions():
                    del queue
    
    async def periodic_event_check(self):
        print(f"Starting async periodic event check.")
        try:
            while True:
                # update timers in all sessions instances
                if self.check_alive_clients():
                    continue
                for queue in self.queues:
                    
                    if isinstance(queue, QueueManager):
                    # client is tuple (ip, queue)
                    # queue check
                        await queue.check_events_server()
                        print(f"--")
                
                # log doesnt spam console
                self.no_overflow = self.no_overflow + 1
                if self.no_overflow > 2:
                    self.no_overflow = 0
                        
                    print(f"\r.")
                    
                   
                # new client connected
                    # is check automaticaly by serve.forever()
                
                await asyncio.sleep(1)
        
            
        except TimeoutError as e :
            print(f"TimeoutError {e}")
            pass
    
        except Exception as e:
            print(f"Exception {e}")
            
        
    async def close(self):
        self._loop.close()


    # Main function
async def main():
    server = ServerIEC104()
    await server.listen()
    await server.run()
        
if __name__ == '__main__':
    
    server = ServerIEC104()
    try:
        # asyncio.run(server.start())
        asyncio.run(main())

    except KeyboardInterrupt:
        pass
    finally:
        pass
