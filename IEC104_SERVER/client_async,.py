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
    def __init__(self):
        self.ssn = 0    # send sequence number
        self.rsn = 0    # receive sequence number
        self.connected = False
        self.k = config_loader.config['client']['k']
        self.w = config_loader.config['client']['w']
        self.servers = []
        self.queue_man = QueueManager()
        self.data = 'vymyslena data'
        self.data = 0x65 + 0x01 + 0x0A + 0x00 + 0x0C + 0x00 + 0x00 + 0x00 + 0x00 + 0x05
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
        print(len(self.data))
        
    async def run_client(self, ip, port):
        
        self.server_address = ip
        self.server_port = port
        
        
        print(f"Vytáčím {self.server_address}:{self.server_port}")
        
        self.reader, self.writer = await asyncio.open_connection(self.server_address, self.server_port)
        
        client_address, client_port =self.writer.get_extra_info('sockname')
        print(f"Navázáno {client_address}:{client_port}-->{self.server_address}:{self.server_port}")
        
        self.servers.append((self.server_address,self.server_port, self.queue_man))
        
        frame1 = UFormat(acpi.STARTDT_ACT)
        self.writer.write(frame1.serialize())
        print(f"{time.ctime()} - Odeslán rámec: {frame1}")
        
        resp = await self.listen()
        
        if isinstance(resp, UFormat):
            
            print(f"{time.ctime()} - Přijat rámec: {resp}")
            frames1 = []
            frames2 = []
            # for i in range(0,1)
            #     frames1.append(UFormat(acpi.TESTFR_ACT))
            #     self.writer.write(frames1[i].serialize())
            #     await self.writer.drain()
            #     print(f"Odeslán rámec: {frames1[i]}")
                
            #     resp = await self.listen()
            #     if isinstance(resp, UFormat):
            #         print(f"Ok, přijat Testdt con")
            #         time.sleep(2)
            #     else:
            #         break
                
            for i in range(0,1):
                frames2.append(IFormat(self.data, self.queue_man.get_VS(), self.queue_man.get_VR()))
                self.queue_man.insert_send_queue(frames2[i])
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
                        #   2-3 - UFormat - startdt seq
                        #   4-5 - UFormat - stopdt seq
                        #   6-7 - UFormat - testdt seq
                        #   >=8 - Chyba
                        
                        if return_code < 8:
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
    client = IEC104Client()
    
    try:
        asyncio.run(client.run_client(config_loader.config['client']['ip_address'], config_loader.config['client']['port']))
    except KeyboardInterrupt:
        pass
    finally:
        pass