# -*- coding: utf-8 -*-
import socket
import binascii
from Parser import Parser
from QueueManager import QueueManager
import acpi
import asdu
import json
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
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.ssn = 0    # send sequence number
        self.rsn = 0    # receive sequence number
        self.connected = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servers = []
        self.queue_man = QueueManager()
        
    async def run_client(self):
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        
        frame1 = UFormat(acpi.STARTDT_ACT)
        self.writer.write(frame1.serialize())
        
        resp = await self.listen()
        
        if isinstance(resp, UFormat):
            print(f"Ok")
        
        if isinstance(resp, IFormat):
            self.queue_man.insert(resp)
            self.queue_man.incrementVR
            self.queue_man.setACK(resp.get_rsn)
            self.queue_man.clear_acked()
        
        if isinstance(resp, SFormat):
            self.queue_man.setACK(resp.get_rsn)
            self.queue_man.clear_acked()
        
        
        
        
        
        self.servers.append(self.writer)
        
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
                                    self.writer.write(response.serialize())
                                return response
                                    
                            
                            await self.writer.drain() 
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
        

if __name__ == "__main__":
    
    config_loader = ConfigLoader('config_parameters.json')
    client = IEC104Client(config_loader.config['client']['ip_address'], config_loader.config['client']['port'])
    
    try:
        asyncio.run(client.run_client())
    except KeyboardInterrupt:
        pass
    finally:
        pass