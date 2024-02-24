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
import Session
import Frame
from QueueManager import QueueManager
from Timeout import Timeout



LISTENER_LIMIT = 5

class ServerIEC104():
    
    # constructor for IEC104 server
    def __init__(self,loop=0): 
        config_loader = ConfigLoader('config_parameters.json')

        self.ip = config_loader.config['server']['ip_address']
        self.port = config_loader.config['server']['port']
        self.active_session = False
        self.connected = False
        self.type_frame = ""
        self.server_clients = []
        
        self.active_clients = [] # List of all currently connected users
    

    # Main function
    async def start(self, loop = 0):
        
        self.server = await asyncio.start_server(
            self.server_handle_client, self.ip, self.port
            )
        async with self.server:
            print(f"Naslouchám na {self.ip}:{self.port}")
            await self.server.serve_forever()


    async def server_handle_client(self, reader, writer):
        
        
        self.queue_man = QueueManager()
        
        self.server_clients.append(writer)
        print(f"Připojen reader: {reader}, writer: {writer}")
        while True:
            try:
                header = await reader.read(2)
                
                if not header:
                    break
                
                start_byte, frame_length = header
                
                if start_byte == Frame.Frame.start_byte:
                    apdu = await reader.read(frame_length)
                    if len(apdu) == frame_length:
                        return_code, new_apdu = Parser.parser(apdu,frame_length)
                        
                        # return_code = 
                        #   0 - IFormat
                        #   1 - SFormat 
                        #   2 - UFormat - startdt seq
                        #   3 - UFormat - stopdt seq
                        #   4 - UFormat - testdt seq
                        #   >=5 - Chyba
                        
                        if return_code < 8:
                            if isinstance(new_apdu, IFormat):
                                self.queue_man.insert(new_apdu)
                                self.queue_man.incrementVR
                                self.queue_man.setACK(new_apdu.get_rsn)
                                self.queue_man.clear_acked()
                                
                            if isinstance(new_apdu, SFormat):
                                self.queue_man.setACK(new_apdu.get_rsn)
                                self.queue_man.clear_acked()
                            
                            if isinstance(new_apdu, UFormat):
                                response = self.queue_man.Uformat(new_apdu)
                                if response:
                                    writer.write(response.serialize())
                                    
                              
                            await writer.drain() 
                            return new_apdu
                        raise Exception(f"Chyba - nejspíš v implementaci, neznámý formát")
                    
                    else:
                        raise Exception("Nastala chyba v přenosu, " 
                                        "přijatá data se nerovnájí požadovaným.")
                    
                else:
                    # zde pak psát logy
                    raise Exception("Přijat neznámý formát")
                
            except Exception as e:
                print(f"Exception {e}")
        

        
            
        
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
