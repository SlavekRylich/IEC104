# -*- coding: utf-8 -*-
import socket
import binascii
import acpi
import asdu
import json
import struct
import logging
from config_loader import ConfigLoader
from CommModule import CommModule
import threading
import Frame
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
        


if __name__ == "__main__":
    
    config_loader = ConfigLoader('config_parameters.json')
    client = IEC104Client(config_loader.config['client']['ip_address'], config_loader.config['client']['port'])
    client.client_socket.connect((client.ip, client.port))
    
    #client.client_socket.settimeout(acpi.T0)
    
    print(client.client_socket.gettimeout())
    comm_module = CommModule(client.client_socket)
    
    #comm_module.send_U_format(acpi.TESTFR_ACT)
    
    time.sleep(3)
    
    comm_module.send_U_format(acpi.TESTFR_ACT)
    
    #threading.Thread(target=comm_module.connection_timeout, args=(client.client_socket,)).start()
        
    # # send startdt
    # data = frame.pack(acpi.STARTDT_ACT)
    # comm_module.send_data(data)
    # data_back = comm_module.receive_data()
    
    # # send testdt
    # data = frame.pack(acpi.TESTFR_ACT)
    # comm_module.send_data(data)
    # data_back = comm_module.receive_data()
    
    # # send testdt
    # data = frame.pack(acpi.TESTFR_ACT)
    # comm_module.send_data(data)
    # data_back = comm_module.receive_data()
    
    # # send testdt
    # data = frame.pack(acpi.TESTFR_ACT)
    # comm_module.send_data(data)
    # data_back = comm_module.receive_data()
    
    # # send stopdt
    # data = frame.pack(acpi.STOPDT_ACT)
    # comm_module.send_data(data)
    # data_back = comm_module.receive_data()
    # client.client_socket.close()
    
    # time.sleep(40)
    # # send startdt
    # data = frame.pack(acpi.STARTDT_ACT)
    # comm_module.send_data(data)
    # data_back = comm_module.receive_data()
    
    # # send stopdt
    # data = frame.pack(acpi.STOPDT_ACT)
    # comm_module.send_data(data)
    # data_back = comm_module.receive_data()
    client.client_socket.close()
    
    # client.comm_module.send_startdt_sequence()
    # client.comm_module.send_stopdt_sequence()
    # client.comm_module.send_testfr_sequence()
    
    
    # Example: Send data to the server
    # client_data = {"message": "Hello from the client!"}
    # start_byte = b'\x68'    
    # client_data_bytes = json.dumps(client_data).encode('utf-8')
    # length_byte = struct.pack("H", len(client_data_bytes))
    # print(len(client_data_bytes))
    # client.send_data(start_byte + length_byte + client_data_bytes)

    # # Example: Receive data from the server
    # server_response = client.receive_data()
    # print(f"Received response from server: {server_response}")
    